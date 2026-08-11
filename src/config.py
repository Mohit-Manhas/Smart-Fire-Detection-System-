"""Configuration helpers for the fire detection applications."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def model_path() -> Path:
    configured = os.getenv("MODEL_PATH")
    if configured:
        return Path(configured)

    packaged_model = PROJECT_ROOT / "models" / "fire.pt"
    legacy_model = PROJECT_ROOT / "fire.pt"
    return packaged_model if packaged_model.exists() else legacy_model


ESP32_BASE_URL = env_str("ESP32_BASE_URL", "http://192.168.4.1")
ESP32_CAM_BASE_URL = env_str("ESP32_CAM_BASE_URL", "http://192.168.4.3")
CAMERA_STREAM_PATH = env_str("CAMERA_STREAM_PATH", "/video_stream")
CONFIDENCE_THRESHOLD = env_float("CONFIDENCE_THRESHOLD", 0.25)
