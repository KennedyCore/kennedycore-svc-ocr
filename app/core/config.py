from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Set


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = Field(default="kennedycore-svc-ocr", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")

    # OCR
    ocr_lang: str = Field(default="es", alias="OCR_LANG")
    ocr_drop_score: float = Field(default=0.30, alias="OCR_DROP_SCORE")

    # Upload
    max_file_mb: int = Field(default=10, alias="MAX_FILE_MB")
    allowed_ext_raw: str = Field(default=".png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff", alias="ALLOWED_EXT")

    # Preprocess
    ocr_target_min_side: int = Field(default=1200, alias="OCR_TARGET_MIN_SIDE")
    ocr_max_side: int = Field(default=2600, alias="OCR_MAX_SIDE")
    ocr_pad_lr_ratio: float = Field(default=0.03, alias="OCR_PAD_LR_RATIO")
    ocr_pad_top_ratio: float = Field(default=0.03, alias="OCR_PAD_TOP_RATIO")
    ocr_pad_bottom_ratio: float = Field(default=0.12, alias="OCR_PAD_BOTTOM_RATIO")
    ocr_pad_min_px: int = Field(default=16, alias="OCR_PAD_MIN_PX")
    ocr_pad_max_px: int = Field(default=256, alias="OCR_PAD_MAX_PX")

    # Fetch by URL
    fetch_timeout_seconds: float = Field(default=20.0, alias="FETCH_TIMEOUT_SECONDS")
    fetch_max_redirects: int = Field(default=5, alias="FETCH_MAX_REDIRECTS")
    allow_private_networks: bool = Field(default=False, alias="ALLOW_PRIVATE_NETWORKS")

    # Problem Details
    problem_base_url: str = Field(default="https://kennedycore.dev/problems/ocr", alias="PROBLEM_BASE_URL")

    @property
    def allowed_ext(self) -> Set[str]:
        return {e.strip().lower() for e in self.allowed_ext_raw.split(",") if e.strip()}

    @property
    def max_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024


settings = Settings()