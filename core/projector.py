import numpy as np
import cv2
from typing import List, Tuple
from utils.logger import app_logger


class Projector:
    def __init__(self, circle_radius: int = 10, color: Tuple[int, int, int] = (0, 0, 255)):
        self.circle_radius = circle_radius
        self.color = color

    def project(self, visible_img: np.ndarray, points: List[Tuple[int, int]], thermal_shape: Tuple[int, int] = None) -> np.ndarray:
        app_logger.info(f"Proyectando {len(points)} puntos sobre imagen visible")

        result = visible_img.copy()
        h, w = result.shape[:2]

        scaled_points = points
        if thermal_shape is not None:
            thermal_h, thermal_w = thermal_shape
            if thermal_h != h or thermal_w != w:
                scale_x = w / thermal_w
                scale_y = h / thermal_h
                scaled_points = [(int(x * scale_x), int(y * scale_y)) for x, y in points]
                app_logger.info(f"Puntos escalados: {scale_x:.4f}x, {scale_y:.4f}y")

        valid_count = 0
        for x, y in scaled_points:
            if 0 <= x < w and 0 <= y < h:
                cv2.circle(result, (x, y), self.circle_radius, self.color, -1)
                cv2.circle(result, (x, y), self.circle_radius + 2, self.color, 2)
                valid_count += 1

        app_logger.info(f"Puntos dibujados: {valid_count}/{len(points)}")
        return result

    def set_circle_params(self, radius: int = None, color: Tuple[int, int, int] = None):
        if radius is not None:
            self.circle_radius = radius
        if color is not None:
            self.color = color