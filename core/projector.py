import numpy as np
import cv2
from typing import List, Optional, Tuple
from utils.logger import app_logger


class Projector:
    """Dibuja las detecciones sobre la imagen visible.

    Equivale al `viscircles(centers, 10, 'Color', 'r')` del script MATLAB: un
    anillo rojo por detección. A diferencia del original, las coordenadas se
    reescalan cuando la térmica y la visible no tienen el mismo tamaño — MATLAB
    dibujaba en coordenadas de la térmica sobre la figura de la visible, lo que
    desplazaba los puntos varios cientos de pixeles en los bordes.
    """

    def __init__(
        self,
        circle_radius: int = 10,
        color: Tuple[int, int, int] = (0, 0, 255),
        thickness: Optional[int] = None,
        filled: bool = False
    ):
        self.circle_radius = circle_radius
        self.color = color
        self.thickness = thickness
        self.filled = filled

    def project(
        self,
        visible_img: np.ndarray,
        points: List[Tuple[int, int]],
        thermal_shape: Tuple[int, int] = None
    ) -> np.ndarray:
        app_logger.info(f"Proyectando {len(points)} puntos sobre imagen visible")

        result = visible_img.copy()
        h, w = result.shape[:2]

        scaled_points = points
        if thermal_shape is not None:
            thermal_h, thermal_w = thermal_shape[:2]
            if thermal_h != h or thermal_w != w:
                scale_x = w / thermal_w
                scale_y = h / thermal_h
                scaled_points = [(int(x * scale_x), int(y * scale_y)) for x, y in points]
                app_logger.info(f"Puntos escalados: {scale_x:.4f}x, {scale_y:.4f}y")

        radius = self._effective_radius(w, h)
        thickness = self.thickness if self.thickness is not None else max(2, radius // 4)

        valid_count = 0
        for x, y in scaled_points:
            if 0 <= x < w and 0 <= y < h:
                if self.filled:
                    cv2.circle(result, (x, y), radius, self.color, -1, lineType=cv2.LINE_AA)
                else:
                    cv2.circle(result, (x, y), radius, self.color, thickness, lineType=cv2.LINE_AA)
                valid_count += 1

        descartados = len(scaled_points) - valid_count
        if descartados:
            app_logger.warning(f"{descartados} puntos quedaron fuera de la imagen visible")
        app_logger.info(f"Puntos dibujados: {valid_count}/{len(points)}")
        return result

    def _effective_radius(self, width: int, height: int) -> int:
        """Escala el radio en imágenes grandes para que el marcador siga siendo visible.

        Un anillo de radio 10 sobre una imagen de ~10000 px se vuelve invisible al
        mostrarla en pantalla; se mantiene el radio del original como mínimo.
        """
        reference = max(width, height)
        return max(self.circle_radius, int(reference / 400))

    def set_circle_params(
        self,
        radius: int = None,
        color: Tuple[int, int, int] = None,
        thickness: int = None,
        filled: bool = None
    ):
        if radius is not None:
            self.circle_radius = radius
        if color is not None:
            self.color = color
        if thickness is not None:
            self.thickness = thickness
        if filled is not None:
            self.filled = filled
