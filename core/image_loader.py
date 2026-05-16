import numpy as np
import tifffile
import cv2
from pathlib import Path
from typing import Tuple, Optional
from utils.logger import app_logger


class ImageLoader:
    @staticmethod
    def load_thermal(path: str) -> np.ndarray:
        app_logger.info(f"Cargando imagen térmica: {path}")
        ext = Path(path).suffix.lower()

        if ext in [".tif", ".tiff"]:
            img = tifffile.imread(path)
            app_logger.info(f"Thermal cargada - forma: {img.shape}, dtype: {img.dtype}")
        else:
            raise ValueError(f"Formato térmico no soportado: {ext}")

        if img is None or img.size == 0:
            raise ValueError("Imagen térmica vacía")

        return img

    @staticmethod
    def load_visible(path: str) -> np.ndarray:
        app_logger.info(f"Cargando imagen visible: {path}")
        ext = Path(path).suffix.lower()

        if ext == ".png":
            img = cv2.imread(path, cv2.IMREAD_COLOR)
        elif ext in [".jpg", ".jpeg"]:
            img = cv2.imread(path, cv2.IMREAD_COLOR)
        else:
            raise ValueError(f"Formato visible no soportado: {ext}")

        if img is None:
            raise ValueError(f"No se pudo cargar imagen visible: {path}")

        app_logger.info(f"Visible cargada - forma: {img.shape}, dtype: {img.dtype}")
        return img

    @staticmethod
    def normalize_thermal(img: np.ndarray, background_value: float = -32767.0) -> np.ndarray:
        valid_mask = img > background_value

        if not np.any(valid_mask):
            app_logger.warning("No hay pixels válidos para normalizar")
            return np.zeros_like(img, dtype=np.float32)

        img_min = img[valid_mask].min()
        img_max = img[valid_mask].max()

        if img_max - img_min == 0:
            return np.zeros_like(img, dtype=np.float32)

        normalized = (img.astype(np.float32) - img_min) / (img_max - img_min)
        normalized[~valid_mask] = 0

        app_logger.debug(f"Thermal normalizada a [0,1] - min: {normalized.min():.4f}, max: {normalized.max():.4f}")
        return normalized

    @staticmethod
    def get_image_info(img: np.ndarray) -> dict:
        return {
            "shape": img.shape,
            "dtype": str(img.dtype),
            "min": float(img.min()) if img.size > 0 else 0,
            "max": float(img.max()) if img.size > 0 else 0,
            "mean": float(img.mean()) if img.size > 0 else 0
        }