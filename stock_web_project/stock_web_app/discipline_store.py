from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from uuid import uuid4


RULE_FIELDS = [
    "id",
    "rule_title",
    "rule_type",
    "rule_content",
    "priority",
    "strong_reminder",
    "status",
    "created_by",
    "created_at",
    "updated_by",
    "updated_at",
    "is_deleted",
]

LESSON_FIELDS = [
    "id",
    "lesson_time",
    "target_name",
    "target_code",
    "concept_name",
    "mistake_action",
    "original_thought",
    "actual_outcome",
    "trigger_reason",
    "linked_rule",
    "improvement_action",
    "severity",
    "show_on_dashboard",
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


class _CsvTable:
    def __init__(self, file_path: str, fields: list[str]):
        self.file_path = Path(file_path)
        self.fields = fields
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
            writer = csv.DictWriter(file_obj, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(rows)


class CsvRuleStore(_CsvTable):
    def __init__(self, file_path: str):
        super().__init__(file_path, RULE_FIELDS)

    def _build_rule(self, payload: dict[str, str], existing: dict[str, str] | None = None) -> dict[str, str]:
        existing = existing or {}
        rule_title = _clean_text(payload.get("rule_title"))
        rule_content = _clean_text(payload.get("rule_content"))

        if not rule_title:
            raise ValueError("请填写规则标题")
        if not rule_content:
            raise ValueError("请填写规则内容")

        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        operator = (
            _clean_text(payload.get("updated_by"))
            or _clean_text(payload.get("created_by"))
            or "system"
        )

        return {
            "id": existing.get("id") if existing else uuid4().hex,
            "rule_title": rule_title,
            "rule_type": _clean_text(payload.get("rule_type")) or "开仓",
            "rule_content": rule_content,
            "priority": _clean_text(payload.get("priority")) or "high",
            "strong_reminder": "1" if _clean_text(payload.get("strong_reminder")).lower() in {"1", "true", "yes", "on"} else "0",
            "status": _clean_text(payload.get("status")) or "active",
            "created_by": _clean_text(existing.get("created_by")) if existing else (_clean_text(payload.get("created_by")) or operator),
            "created_at": _clean_text(existing.get("created_at")) if existing else now_text,
            "updated_by": operator,
            "updated_at": now_text,
            "is_deleted": _clean_text(existing.get("is_deleted", "0")) if existing else "0",
        }

    def list_rules(self, limit: int | None = None) -> list[dict[str, str]]:
        rows = [row for row in self._read_rows() if _clean_text(row.get("is_deleted", "0")) != "1"]
        priority_order = {"high": 0, "medium": 1, "low": 2}

        def _sort_key(row: dict[str, str]):
            try:
                updated_at = _parse_datetime(_clean_text(row.get("updated_at", "")))
                updated_order = -updated_at.timestamp()
            except ValueError:
                updated_order = 0

            return (
                _clean_text(row.get("strong_reminder", "0")) != "1",
                priority_order.get(_clean_text(row.get("priority", "medium")), 9),
                updated_order,
            )

        rows.sort(key=_sort_key)
        if limit is not None and limit > 0:
            return rows[:limit]
        return rows

    def create_rule(self, payload: dict[str, str]) -> dict[str, str]:
        row = self._build_rule(payload)
        rows = self._read_rows()
        rows.append(row)
        self._write_rows(rows)
        return row

    def update_rule(self, rule_id: str, payload: dict[str, str]) -> dict[str, str]:
        rows = self._read_rows()
        for index, row in enumerate(rows):
            if row.get("id") != rule_id or _clean_text(row.get("is_deleted", "0")) == "1":
                continue

            updated_row = self._build_rule(payload, existing=row)
            rows[index] = updated_row
            self._write_rows(rows)
            return updated_row

        raise ValueError("未找到可更新的纪律清单")

    def delete_rule(self, rule_id: str, operator: str = "system") -> dict[str, str]:
        rows = self._read_rows()
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for index, row in enumerate(rows):
            if row.get("id") != rule_id or _clean_text(row.get("is_deleted", "0")) == "1":
                continue

            row["is_deleted"] = "1"
            row["updated_by"] = operator or "system"
            row["updated_at"] = now_text
            rows[index] = row
            self._write_rows(rows)
            return row

        raise ValueError("未找到可删除的纪律清单")


class CsvLessonStore(_CsvTable):
    def __init__(self, file_path: str):
        super().__init__(file_path, LESSON_FIELDS)

    def _build_lesson(self, payload: dict[str, str], existing: dict[str, str] | None = None) -> dict[str, str]:
        existing = existing or {}
        lesson_time = _clean_text(payload.get("lesson_time"))
        mistake_action = _clean_text(payload.get("mistake_action"))
        actual_outcome = _clean_text(payload.get("actual_outcome"))

        if not lesson_time:
            raise ValueError("请填写时间")
        if not mistake_action:
            raise ValueError("请填写错误行为")
        if not actual_outcome:
            raise ValueError("请填写实际后果")

        normalized_time = _parse_datetime(lesson_time).strftime("%Y-%m-%d %H:%M:%S")
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        operator = (
            _clean_text(payload.get("updated_by"))
            or _clean_text(payload.get("created_by"))
            or "system"
        )

        return {
            "id": existing.get("id") if existing else uuid4().hex,
            "lesson_time": normalized_time,
            "target_name": _clean_text(payload.get("target_name")),
            "target_code": _clean_text(payload.get("target_code")),
            "concept_name": _clean_text(payload.get("concept_name")),
            "mistake_action": mistake_action,
            "original_thought": _clean_text(payload.get("original_thought")),
            "actual_outcome": actual_outcome,
            "trigger_reason": _clean_text(payload.get("trigger_reason")),
            "linked_rule": _clean_text(payload.get("linked_rule")),
            "improvement_action": _clean_text(payload.get("improvement_action")),
            "severity": _clean_text(payload.get("severity")) or "high",
            "show_on_dashboard": "1" if _clean_text(payload.get("show_on_dashboard")).lower() in {"1", "true", "yes", "on"} else "0",
            "created_by": _clean_text(existing.get("created_by")) if existing else (_clean_text(payload.get("created_by")) or operator),
            "created_at": _clean_text(existing.get("created_at")) if existing else now_text,
            "updated_by": operator,
            "updated_at": now_text,
            "is_deleted": _clean_text(existing.get("is_deleted", "0")) if existing else "0",
        }

    def list_lessons(self, limit: int | None = None, dashboard_only: bool = False) -> list[dict[str, str]]:
        rows = [row for row in self._read_rows() if _clean_text(row.get("is_deleted", "0")) != "1"]
        if dashboard_only:
            rows = [row for row in rows if _clean_text(row.get("show_on_dashboard", "0")) == "1"]

        def _sort_key(row: dict[str, str]):
            try:
                lesson_time = _parse_datetime(_clean_text(row.get("lesson_time", "")))
            except ValueError:
                lesson_time = datetime.min
            return lesson_time

        rows.sort(key=_sort_key, reverse=True)
        if limit is not None and limit > 0:
            return rows[:limit]
        return rows

    def create_lesson(self, payload: dict[str, str]) -> dict[str, str]:
        row = self._build_lesson(payload)
        rows = self._read_rows()
        rows.append(row)
        self._write_rows(rows)
        return row

    def update_lesson(self, lesson_id: str, payload: dict[str, str]) -> dict[str, str]:
        rows = self._read_rows()
        for index, row in enumerate(rows):
            if row.get("id") != lesson_id or _clean_text(row.get("is_deleted", "0")) == "1":
                continue

            updated_row = self._build_lesson(payload, existing=row)
            rows[index] = updated_row
            self._write_rows(rows)
            return updated_row

        raise ValueError("未找到可更新的血泪教训")

    def delete_lesson(self, lesson_id: str, operator: str = "system") -> dict[str, str]:
        rows = self._read_rows()
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for index, row in enumerate(rows):
            if row.get("id") != lesson_id or _clean_text(row.get("is_deleted", "0")) == "1":
                continue

            row["is_deleted"] = "1"
            row["updated_by"] = operator or "system"
            row["updated_at"] = now_text
            rows[index] = row
            self._write_rows(rows)
            return row

        raise ValueError("未找到可删除的血泪教训")
