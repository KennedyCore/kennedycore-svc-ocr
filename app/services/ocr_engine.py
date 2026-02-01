from __future__ import annotations

from typing import Any, Dict, List, Optional
import threading

import cv2
import numpy as np
from paddleocr import PaddleOCR

from app.core.config import settings
from app.services.image_preprocess import PreprocessConfig, preprocess_for_ocr


class PaddleOcrEngine:
    def __init__(self) -> None:
        self._lock = threading.Lock()

        self._pp_cfg = PreprocessConfig(
            target_min_side=settings.ocr_target_min_side,
            max_side=settings.ocr_max_side,
            pad_lr_ratio=settings.ocr_pad_lr_ratio,
            pad_top_ratio=settings.ocr_pad_top_ratio,
            pad_bottom_ratio=settings.ocr_pad_bottom_ratio,
            pad_min_px=settings.ocr_pad_min_px,
            pad_max_px=settings.ocr_pad_max_px,
        )

        self._ocr = PaddleOCR(
            use_angle_cls=True,
            lang=settings.ocr_lang,
            drop_score=settings.ocr_drop_score,
        )

    def extract_from_bytes(self, data: bytes, *, preprocess: bool, return_blocks: bool) -> Dict[str, Any]:
        img = self._decode_image(data)
        return self.extract(img, preprocess=preprocess, return_blocks=return_blocks)

    def extract(self, img_bgr: np.ndarray, *, preprocess: bool, return_blocks: bool) -> Dict[str, Any]:
        meta: Optional[Dict[str, Any]] = None
        if preprocess:
            img_bgr, meta = preprocess_for_ocr(img_bgr, self._pp_cfg)

        result = self._run_ocr(img_bgr)

        blocks: List[Dict[str, Any]] = []
        lines: List[str] = []

        if result:
            for page in result:
                if not page:
                    continue
                for line in page:
                    if not line or len(line) < 2:
                        continue
                    box = line[0]
                    text = str(line[1][0]).strip()
                    conf = float(line[1][1])

                    if text:
                        lines.append(text)

                    if return_blocks:
                        blocks.append(
                            {
                                "text": text,
                                "confidence": conf,
                                "box": [[int(round(p[0])), int(round(p[1]))] for p in box],
                            }
                        )

        return {
            "text": "\n".join(lines).strip(),
            "blocks": blocks if return_blocks else [],
            "preprocess": meta,
        }

    def _run_ocr(self, img_bgr: np.ndarray):
        with self._lock:
            return self._ocr.ocr(img_bgr, cls=True)

    def _decode_image(self, data: bytes) -> np.ndarray:
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image bytes (decode failed)")
        return img