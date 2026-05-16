import numpy as np
from skimage import measure, morphology
from typing import List, Tuple
from utils.logger import app_logger


class BlobAnalyzer:
    def __init__(
        self,
        min_area: int = 10,
        max_area: int = 5000,
        morph_kernel_size: int = 3
    ):
        self.min_area = min_area
        self.max_area = max_area
        self.morph_kernel_size = morph_kernel_size

    def analyze(self, binary_mask: np.ndarray) -> List[Tuple[int, int]]:
        app_logger.info(f"Analizando blobs - área mínima: {self.min_area}, máxima: {self.max_area}")

        cleaned = self._apply_morphology(binary_mask)

        labeled = measure.label(cleaned, connectivity=2)
        app_logger.debug(f"Etiquetas generadas - {labeled.max()} componentes encontrados")

        regions = measure.regionprops(labeled)

        centroids = []
        for region in regions:
            if self.min_area <= region.area <= self.max_area:
                cy, cx = region.centroid
                centroids.append((int(cx), int(cy)))

        app_logger.info(f"Blobs válidos después de filtrado: {len(centroids)}")
        return centroids

    def analyze_points(self, points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        if not points:
            return []

        app_logger.info(f"Agrupando {len(points)} puntos detectados")

        points_arr = np.array(points)
        min_x, min_y = points_arr.min(axis=0)
        max_x, max_y = points_arr.max(axis=0)

        height = max_y - min_y + 1
        width = max_x - min_x + 1

        mask = np.zeros((height, width), dtype=bool)
        for x, y in points:
            mask[y - min_y, x - min_x] = True

        cleaned = self._apply_morphology(mask)

        labeled = measure.label(cleaned, connectivity=2)
        regions = measure.regionprops(labeled)

        centroids = []
        for region in regions:
            if self.min_area <= region.area <= self.max_area:
                cy, cx = region.centroid
                cx = int(cx + min_x)
                cy = int(cy + min_y)
                centroids.append((cx, cy))

        app_logger.info(f"Blobs agrupados: {len(centroids)}")
        return centroids

    def _apply_morphology(self, binary_mask: np.ndarray) -> np.ndarray:
        if self.morph_kernel_size > 0:
            kernel = morphology.disk(self.morph_kernel_size // 2)
            cleaned = morphology.opening(binary_mask, kernel)
            cleaned = morphology.closing(cleaned, kernel)
            removed = morphology.remove_small_objects(cleaned, min_size=self.min_area)
            app_logger.debug(f"Morfología aplicada - pixels restantes: {np.sum(removed)}")
            return removed
        return binary_mask

    def set_parameters(self, min_area: int = None, max_area: int = None):
        if min_area is not None:
            self.min_area = min_area
            app_logger.info(f"Área mínima actualizada: {min_area}")
        if max_area is not None:
            self.max_area = max_area
            app_logger.info(f"Área máxima actualizada: {max_area}")