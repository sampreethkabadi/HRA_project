from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DatasetPaths:
    hra_logs_parquet: Path
    duckdb_path: Path


@dataclass(frozen=True)
class Settings:
    paths: DatasetPaths
    excluded_traffic_types: tuple[str, ...]
    performance_app_segments: dict[str, str]


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_settings(config_path: str | Path) -> Settings:
    config_file = Path(config_path).resolve()
    raw = _read_yaml(config_file)
    project_root = config_file.parents[1]

    def _resolve(maybe_path: str) -> Path:
        candidate = Path(maybe_path).expanduser()
        if candidate.is_absolute():
            return candidate
        return (project_root / candidate).resolve()

    return Settings(
        paths=DatasetPaths(
            hra_logs_parquet=_resolve(raw["datasets"]["hra_logs_parquet"]),
            duckdb_path=_resolve(raw["database"]["duckdb_path"]),
        ),
        excluded_traffic_types=tuple(raw["filters"]["excluded_traffic_types"]),
        performance_app_segments=dict(raw["performance"]["app_segments"]),
    )
