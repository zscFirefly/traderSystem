from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


PRESET_FIELDS = [
    "id",
    "name",
    "description",
    "stocks_json",
    "trading_days",
    "period",
    "include_heatmaps",
    "is_pinned",
    "created_by",
    "created_at",
    "updated_by",
    "updated_at",
    "is_deleted",
]


def _clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_stocks(value) -> list[dict[str, str]]:
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("请至少提供一只股票")
        try:
            stocks = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("股票池格式错误") from exc
    else:
        stocks = value

    if not isinstance(stocks, list) or not stocks:
        raise ValueError("请至少提供一只股票")

    normalized = []
    seen_codes = set()
    for item in stocks:
        if not isinstance(item, dict):
            raise ValueError("股票池格式错误")
        stock_code = _clean_text(item.get("stock_code"))
        stock_name = _clean_text(item.get("stock_name"))
        if not stock_code or not stock_name:
            raise ValueError("股票池中的每只股票都需要 stock_code 和 stock_name")
        if stock_code in seen_codes:
            continue
        seen_codes.add(stock_code)
        normalized.append({"stock_code": stock_code, "stock_name": stock_name})

    if not normalized:
        raise ValueError("请至少提供一只股票")
    return normalized


class CsvCorrelationPresetStore:
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
            writer = csv.DictWriter(file_obj, fieldnames=PRESET_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def _serialize(self, row: dict[str, str]) -> dict[str, object]:
        serialized = dict(row)
        serialized["stocks"] = json.loads(serialized.pop("stocks_json", "[]"))
        serialized["trading_days"] = int(_clean_text(serialized.get("trading_days")) or "10")
        serialized["include_heatmaps"] = _clean_text(serialized.get("include_heatmaps")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        serialized["is_pinned"] = _clean_text(serialized.get("is_pinned")).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return serialized

    def _build_preset(self, payload: dict[str, object], existing: dict[str, str] | None = None) -> dict[str, str]:
        existing = existing or {}
        name = _clean_text(payload.get("name"))
        description = _clean_text(payload.get("description"))
        stocks = _parse_stocks(payload.get("stocks") or payload.get("stocks_json"))
        trading_days_raw = _clean_text(payload.get("trading_days")) or "10"
        period = _clean_text(payload.get("period")) or "5"

        if not name:
            raise ValueError("请填写方案名称")

        try:
            trading_days = int(trading_days_raw)
        except ValueError as exc:
            raise ValueError("trading_days 必须是整数") from exc
        if trading_days <= 0:
            raise ValueError("trading_days 必须大于 0")

        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        operator = (
            _clean_text(payload.get("updated_by"))
            or _clean_text(payload.get("created_by"))
            or "system"
        )

        return {
            "id": existing.get("id") if existing else uuid4().hex,
            "name": name,
            "description": description,
            "stocks_json": json.dumps(stocks, ensure_ascii=False),
            "trading_days": str(trading_days),
            "period": period,
            "include_heatmaps": (
                "1"
                if _clean_text(payload.get("include_heatmaps")).lower() in {"1", "true", "yes", "on"}
                else "0"
            ),
            "is_pinned": (
                "1"
                if _clean_text(payload.get("is_pinned")).lower() in {"1", "true", "yes", "on"}
                else "0"
            ),
            "created_by": _clean_text(existing.get("created_by")) if existing else (_clean_text(payload.get("created_by")) or operator),
            "created_at": _clean_text(existing.get("created_at")) if existing else now_text,
            "updated_by": operator,
            "updated_at": now_text,
            "is_deleted": _clean_text(existing.get("is_deleted", "0")) if existing else "0",
        }

    def list_presets(self, limit: int | None = None) -> list[dict[str, object]]:
        rows = [row for row in self._read_rows() if _clean_text(row.get("is_deleted", "0")) != "1"]

        def _sort_key(row: dict[str, str]):
            try:
                updated_at = datetime.strptime(
                    _clean_text(row.get("updated_at")) or "1970-01-01 00:00:00",
                    "%Y-%m-%d %H:%M:%S",
                )
                updated_order = -updated_at.timestamp()
            except ValueError:
                updated_order = 0

            return (
                _clean_text(row.get("is_pinned", "0")) != "1",
                updated_order,
            )

        rows.sort(key=_sort_key)
        if limit is not None and limit > 0:
            rows = rows[:limit]
        return [self._serialize(row) for row in rows]

    def create_preset(self, payload: dict[str, object]) -> dict[str, object]:
        row = self._build_preset(payload)
        rows = self._read_rows()
        rows.append(row)
        self._write_rows(rows)
        return self._serialize(row)

    def update_preset(self, preset_id: str, payload: dict[str, object]) -> dict[str, object]:
        rows = self._read_rows()
        for index, row in enumerate(rows):
            if row.get("id") != preset_id or _clean_text(row.get("is_deleted", "0")) == "1":
                continue

            updated_row = self._build_preset(payload, existing=row)
            rows[index] = updated_row
            self._write_rows(rows)
            return self._serialize(updated_row)

        raise ValueError("未找到可更新的相关性方案")

    def delete_preset(self, preset_id: str, operator: str = "system") -> dict[str, object]:
        rows = self._read_rows()
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for index, row in enumerate(rows):
            if row.get("id") != preset_id or _clean_text(row.get("is_deleted", "0")) == "1":
                continue

            row["is_deleted"] = "1"
            row["updated_by"] = operator or "system"
            row["updated_at"] = now_text
            rows[index] = row
            self._write_rows(rows)
            return self._serialize(row)

        raise ValueError("未找到可删除的相关性方案")
