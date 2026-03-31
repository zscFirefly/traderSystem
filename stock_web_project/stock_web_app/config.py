import os
from pathlib import Path


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_data_file() -> str:
    project_root = Path(__file__).resolve().parents[1]
    parent_root = project_root.parent
    filenames = [
        "板块涨停_关系型_全量.xlsx",
        "板块涨停_关系型_全量_org.xlsx",
    ]

    candidates = []
    for filename in filenames:
        candidates.extend(
            [
                project_root / "data" / filename,
                project_root / filename,
                parent_root / filename,
            ]
        )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return str(project_root / "data" / filenames[0])


class Config:
    DEBUG = _to_bool(os.getenv("FLASK_DEBUG"), default=True)
    HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_RUN_PORT", "8080"))
    DATA_FILE = os.getenv("STOCK_DATA_FILE", resolve_data_file())
    DATA_SHEET = os.getenv("STOCK_DATA_SHEET", "股票维度")
    ALERTS_FILE = os.getenv(
        "EVENT_ALERTS_FILE",
        str(Path(__file__).resolve().parents[1] / "data" / "event_alerts.csv"),
    )
    TRADING_RULES_FILE = os.getenv(
        "TRADING_RULES_FILE",
        str(Path(__file__).resolve().parents[1] / "data" / "trading_rules.csv"),
    )
    TRADING_LESSONS_FILE = os.getenv(
        "TRADING_LESSONS_FILE",
        str(Path(__file__).resolve().parents[1] / "data" / "trading_lessons.csv"),
    )
    CORRELATION_PRESETS_FILE = os.getenv(
        "CORRELATION_PRESETS_FILE",
        str(Path(__file__).resolve().parents[1] / "data" / "correlation_presets.csv"),
    )
