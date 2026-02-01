from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class PreprocessConfig:
    target_min_side: int
    max_side: int
    pad_lr_ratio: float
    pad_top_ratio: float
    pad_bottom_ratio: float
    pad_min_px: int
    pad_max_px: int


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def preprocess_for_ocr(img_bgr: np.ndarray, cfg: PreprocessConfig) -> Tuple[np.ndarray, Dict]:
    if img_bgr is None or img_bgr.size == 0:
        raise ValueError("Empty image")

    if img_bgr.dtype != np.uint8:
        img_bgr = img_bgr.astype(np.uint8)

    h, w = img_bgr.shape[:2]

    pad_lr = _clamp(int(w * cfg.pad_lr_ratio), cfg.pad_min_px, cfg.pad_max_px)
    pad_top = _clamp(int(h * cfg.pad_top_ratio), cfg.pad_min_px, cfg.pad_max_px)
    pad_bottom = _clamp(int(h * cfg.pad_bottom_ratio), cfg.pad_min_px, cfg.pad_max_px)

    padded = cv2.copyMakeBorder(
        img_bgr,
        top=pad_top,
        bottom=pad_bottom,
        left=pad_lr,
        right=pad_lr,
        borderType=cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )

    ph, pw = padded.shape[:2]
    min_side = min(ph, pw)
    max_side = max(ph, pw)

    scale = 1.0
    if min_side < cfg.target_min_side:
        scale = cfg.target_min_side / float(min_side)
    if max_side * scale > cfg.max_side:
        scale = cfg.max_side / float(max_side)

    if abs(scale - 1.0) >= 0.03:
        interp = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_AREA
        new_w = int(round(pw * scale))
        new_h = int(round(ph * scale))
        out = cv2.resize(padded, (new_w, new_h), interpolation=interp)
    else:
        out = padded

    meta = {
        "padding": {"left": pad_lr, "right": pad_lr, "top": pad_top, "bottom": pad_bottom},
        "scale": scale,
        "original_shape": {"h": h, "w": w},
        "padded_shape": {"h": ph, "w": pw},
        "final_shape": {"h": out.shape[0], "w": out.shape[1]},
    }
    return out, meta