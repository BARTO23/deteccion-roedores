import numpy as np
from typing import Tuple, List
from utils.logger import app_logger


class ThermalDetector:
    def __init__(
        self,
        threshold: float = 0.56,
        min_area: int = 10,
        max_area: int = 5000,
        background_value: float = -32767.0
    ):
        self.threshold = threshold
        self.min_area = min_area
        self.max_area = max_area
        self.background_value = background_value

    def detect_matlab_style(self, img: np.ndarray) -> List[Tuple[int, int]]:
        app_logger.info(f"Ejecutando detección estilo MATLAB con T={self.threshold}")

        if img.dtype != np.float32:
            img = img.astype(np.float32)

        valid_mask = img > self.background_value
        if not np.any(valid_mask):
            app_logger.warning("No hay pixels válidos en la imagen")
            return []

        working_img = img.copy()
        working_img[~valid_mask] = 0

        pad = np.pad(working_img, 1, mode='constant', constant_values=0)
        mask_pad = np.pad(valid_mask, 1, mode='constant', constant_values=False)

        center = pad[1:-1, 1:-1]

        neighbor_right = pad[1:-1, 2:]
        neighbor_up = pad[2:, 1:-1]
        neighbor_left = pad[1:-1, :-2]
        neighbor_down = pad[:-2, 1:-1]

        mask_right = mask_pad[1:-1, 2:]
        mask_up = mask_pad[2:, 1:-1]
        mask_left = mask_pad[1:-1, :-2]
        mask_down = mask_pad[:-2, 1:-1]

        neighbor_sum = np.where(mask_right, neighbor_right, 0) + \
                       np.where(mask_up, neighbor_up, 0) + \
                       np.where(mask_left, neighbor_left, 0) + \
                       np.where(mask_down, neighbor_down, 0)

        neighbor_count = mask_right.astype(int) + mask_up.astype(int) + \
                         mask_left.astype(int) + mask_down.astype(int)

        with np.errstate(divide='ignore', invalid='ignore'):
            neighbor_avg = np.where(neighbor_count > 0, neighbor_sum / neighbor_count, 0)

        diff = center - neighbor_avg

        binary = diff > self.threshold

        y_coords, x_coords = np.where(binary)
        detected = list(zip(x_coords.tolist(), y_coords.tolist()))

        app_logger.info(f"Puntos detectados por método MATLAB: {len(detected)}")
        return detected

    def detect_threshold(self, img: np.ndarray) -> np.ndarray:
        app_logger.info(f"Ejecutando detección por umbral: {self.threshold}")

        if img.dtype != np.float32:
            img = img.astype(np.float32)

        valid_mask = img > self.background_value

        if not np.any(valid_mask):
            app_logger.warning("No hay pixels válidos en la imagen")
            return np.zeros_like(img, dtype=bool)

        valid_min = img[valid_mask].min()
        valid_max = img[valid_mask].max()

        if valid_max - valid_min == 0:
            return np.zeros_like(img, dtype=bool)

        normalized = img.copy()
        normalized[~valid_mask] = 0
        normalized = (normalized - valid_min) / (valid_max - valid_min)

        binary = normalized > self.threshold
        app_logger.info(f"Máscara binaria - pixels activos: {np.sum(binary)}")
        return binary

    def set_threshold(self, value: float):
        if 0.0 <= value <= 1.0:
            self.threshold = value
            app_logger.info(f"Umbral actualizado a {value}")
        else:
            raise ValueError("El umbral debe estar entre 0.0 y 1.0")