from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from uuid import uuid4


ALERT_FIELDS = [
    "id",
    "event_time",
    "event_title",
    "potential_risk",
    "stock_name",
    "stock_code",
    "concept_name",
    "severity",
    "status",
    "notes",
    "created_by",
    "created_at",
    "updated_by",
    "updated_at",
    "is_deleted",
]


def _parse_datetime(value: str) -> datetime:
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"无法识别的时间格式: {value}")


def _clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


class CsvAlertStore:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_rows([])

    def _read_rows(self) -> list[dict[str, str]]:
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8-sig", newline="") as file_obj:
            reader = csv.DictReader(file_obj)
            return [dict(row) for row in reader]

    def _write_rows(self, rows: list[dict[str, str]]) -> None:
        with self.file_path.open("w", encoding="utf-8-sig", newline="") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=ALERT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def list_alerts(self, limit: int | None = None) -> list[dict[str, str]]:
        rows = [row for row in self._read_rows() if str(row.get("is_deleted", "0")) != "1"]

        def _sort_key(row: dict[str, str]):
            try:
                event_time = _parse_datetime(row.get("event_time", ""))
            except ValueError:
                event_time = datetime.min

            try:
                created_at = _parse_datetime(row.get("created_at", ""))
            except ValueError:
                created_at = datetime.min

            return (event_time, created_at)

        rows.sort(key=_sort_key)
        if limit is not None and limit > 0:
            return rows[:limit]
        return rows

    def _build_payload(self, payload: dict[str, str], existing: dict[str, str] | None = None) -> dict[str, str]:
        existing = existing or {}
        event_time = _clean_text(payload.get("event_time", ""))
        event_title = _clean_text(payload.get("event_title", ""))
        potential_risk = _clean_text(payload.get("potential_risk", ""))

        if not event_time:
            raise ValueError("请填写时间节点")
        if not event_title:
            raise ValueError("请填写事件")
        if not potential_risk:
            raise ValueError("请填写潜在风险")

        normalized_event_time = _parse_datetime(event_time).strftime("%Y-%m-%d %H:%M:%S")
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        operator = (
            _clean_text(payload.get("updated_by", ""))
            or _clean_text(payload.get("created_by", ""))
            or "system"
        )

        row = {
            "id": existing.get("id") if existing else uuid4().hex,
            "event_time": normalized_event_time,
            "event_title": event_title,
            "potential_risk": potential_risk,
            "stock_name": _clean_text(payload.get("stock_name", "")),
            "stock_code": _clean_text(payload.get("stock_code", "")),
            "concept_name": _clean_text(payload.get("concept_name", "")),
            "severity": _clean_text(payload.get("severity", "")) or "medium",
            "status": _clean_text(payload.get("status", "")) or "pending",
            "notes": _clean_text(payload.get("notes", "")),
            "created_by": _clean_text(existing.get("created_by")) if existing else (_clean_text(payload.get("created_by", "")) or operator),
            "created_at": _clean_text(existing.get("created_at")) if existing else now_text,
            "updated_by": operator,
            "updated_at": now_text,
            "is_deleted": _clean_text(existing.get("is_deleted", "0")) if existing else "0",
        }
        return row

    def create_alert(self, payload: dict[str, str]) -> dict[str, str]:
        row = self._build_payload(payload)

        rows = self._read_rows()
        rows.append(row)
        self._write_rows(rows)
        return row

    def update_alert(self, alert_id: str, payload: dict[str, str]) -> dict[str, str]:
        rows = self._read_rows()
        for index, row in enumerate(rows):
            if row.get("id") != alert_id or str(row.get("is_deleted", "0")) == "1":
                continue

            updated_row = self._build_payload(payload, existing=row)
            rows[index] = updated_row
            self._write_rows(rows)
            return updated_row

        raise ValueError("未找到可更新的事件提醒")

    def delete_alert(self, alert_id: str, operator: str = "system") -> dict[str, str]:
        rows = self._read_rows()
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for index, row in enumerate(rows):
            if row.get("id") != alert_id or str(row.get("is_deleted", "0")) == "1":
                continue

            row["is_deleted"] = "1"
            row["updated_by"] = operator or "system"
            row["updated_at"] = now_text
            rows[index] = row
            self._write_rows(rows)
            return row

        raise ValueError("未找到可删除的事件提醒")
