import numpy as np
from typing import Callable, List, Optional, Tuple
from utils.logger import app_logger

# Constantes del script MATLAB original ("identificación de roedores").
MATLAB_THRESHOLD = 0.56      # T: sensibilidad, delta mínimo de temperatura
MATLAB_MAX_DELTA = 1000.0    # cota superior que descarta el fondo de la imagen
MATLAB_MIN_NEIGHBORS = 3     # el original cuenta el pixel cuando c > 2


class ThermalDetector:
    """Replica el detector del script MATLAB original.

    Para cada pixel interior (x = 2..W-1, y = 2..H-1 en índices MATLAB) compara
    el pixel central B contra sus 4 vecinos ortogonales de forma independiente:

        b = abs(abs(B) - abs(vecino))
        cuenta si  B > vecino  y  T < b < 1000

    Si al menos `min_neighbors` de los 4 vecinos cumplen, marca detección.
    La cota `b < 1000` es la que descarta los pixeles de fondo (-32767) sin
    necesidad de una máscara explícita: la diferencia contra el fondo es enorme.
    """

    def __init__(
        self,
        threshold: float = MATLAB_THRESHOLD,
        max_delta: float = MATLAB_MAX_DELTA,
        min_neighbors: int = MATLAB_MIN_NEIGHBORS,
        background_value: float = -32767.0,
        chunk_rows: int = 512
    ):
        self.threshold = threshold
        self.max_delta = max_delta
        self.min_neighbors = min_neighbors
        self.background_value = background_value
        self.chunk_rows = chunk_rows

    def detect_matlab_style(
        self,
        img: np.ndarray,
        progress_cb: Optional[Callable[[int], None]] = None
    ) -> List[Tuple[int, int]]:
        """Devuelve las coordenadas (x, y) de cada pixel detectado.

        Vectoriza el doble ciclo del original por bloques de filas: mismo
        resultado que recorrer pixel a pixel, pero sin materializar copias del
        tamaño completo de la imagen (las térmicas rondan los 90 M de pixeles).
        """
        app_logger.info(
            f"Detección MATLAB - T={self.threshold}, max_delta={self.max_delta}, "
            f"min_vecinos={self.min_neighbors}"
        )

        if img.ndim != 2:
            raise ValueError(f"La imagen térmica debe ser 2D, recibida forma {img.shape}")

        if img.dtype != np.float32:
            img = img.astype(np.float32)

        h, w = img.shape
        if h < 3 or w < 3:
            app_logger.warning("Imagen demasiado pequeña para analizar vecinos")
            return []

        points: List[Tuple[int, int]] = []
        total_rows = h - 2

        for r0 in range(1, h - 1, self.chunk_rows):
            r1 = min(r0 + self.chunk_rows, h - 1)

            center = img[r0:r1, 1:-1]
            abs_center = np.abs(center)

            neighbors = (
                img[r0:r1, 2:],            # derecha    Q(y, x+1)
                img[r0 - 1:r1 - 1, 1:-1],  # superior   Q(y-1, x)
                img[r0:r1, :-2],           # izquierda  Q(y, x-1)
                img[r0 + 1:r1 + 1, 1:-1],  # inferior   Q(y+1, x)
            )

            hits = np.zeros(center.shape, dtype=np.uint8)
            for neighbor in neighbors:
                delta = np.abs(abs_center - np.abs(neighbor))
                cond = (center > neighbor) & (delta < self.max_delta) & (delta > self.threshold)
                hits += cond.view(np.uint8)

            ys, xs = np.nonzero(hits >= self.min_neighbors)
            # +1 en x por el recorte de la columna 0; +r0 en y por el bloque.
            points.extend(zip((xs + 1).tolist(), (ys + r0).tolist()))

            if progress_cb is not None:
                progress_cb(min(100, int((r1 - 1) * 100 / total_rows)))

        app_logger.info(f"Pixeles detectados: {len(points)}")
        return points

    def detect_mask(
        self,
        img: np.ndarray,
        progress_cb: Optional[Callable[[int], None]] = None
    ) -> np.ndarray:
        """Igual que `detect_matlab_style` pero devuelve la máscara booleana."""
        mask = np.zeros(img.shape, dtype=bool)
        for x, y in self.detect_matlab_style(img, progress_cb):
            mask[y, x] = True
        return mask

    def set_threshold(self, value: float):
        # T es un delta de temperatura en las unidades de la imagen térmica,
        # no un valor normalizado: su cota superior es max_delta.
        if not 0.0 <= value < self.max_delta:
            raise ValueError(f"El umbral debe estar entre 0.0 y {self.max_delta}")
        self.threshold = value
        app_logger.info(f"Umbral actualizado a {value}")

    def set_parameters(
        self,
        threshold: Optional[float] = None,
        max_delta: Optional[float] = None,
        min_neighbors: Optional[int] = None
    ):
        if max_delta is not None:
            self.max_delta = max_delta
        if threshold is not None:
            self.set_threshold(threshold)
        if min_neighbors is not None:
            if not 1 <= min_neighbors <= 4:
                raise ValueError("min_neighbors debe estar entre 1 y 4")
            self.min_neighbors = min_neighbors
