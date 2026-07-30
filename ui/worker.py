import numpy as np
from typing import List, Optional, Tuple
from PySide6.QtCore import QThread, Signal

from core.blob_analyzer import BlobAnalyzer
from core.detector import ThermalDetector
from core.projector import Projector


class DetectionWorker(QThread):
    """Corre detección, agrupamiento y proyección fuera del hilo de UI."""

    progress = Signal(int)
    stage = Signal(str)
    finished_ok = Signal(list, int, np.ndarray)
    failed = Signal(str)

    def __init__(
        self,
        detector: ThermalDetector,
        projector: Projector,
        thermal_img: np.ndarray,
        visible_img: np.ndarray,
        threshold: float,
        min_neighbors: int = 3,
        cluster: bool = False,
        merge_radius: int = 3,
        parent=None
    ):
        super().__init__(parent)
        self.detector = detector
        self.projector = projector
        self.thermal_img = thermal_img
        self.visible_img = visible_img
        self.threshold = threshold
        self.min_neighbors = min_neighbors
        self.cluster = cluster
        self.merge_radius = merge_radius

    def run(self):
        try:
            self.detector.set_parameters(
                threshold=self.threshold,
                min_neighbors=self.min_neighbors
            )

            self.stage.emit("Analizando imagen térmica...")
            pixels: List[Tuple[int, int]] = self.detector.detect_matlab_style(
                self.thermal_img, progress_cb=self.progress.emit
            )
            pixel_count = len(pixels)

            points = pixels
            if self.cluster and pixels:
                self.stage.emit("Agrupando detecciones vecinas...")
                points = BlobAnalyzer().cluster_points(pixels, merge_radius=self.merge_radius)

            self.stage.emit("Proyectando sobre imagen visible...")
            result_img = self.projector.project(
                self.visible_img, points, self.thermal_img.shape
            )

            self.progress.emit(100)
            self.finished_ok.emit(points, pixel_count, result_img)
        except Exception as e:
            self.failed.emit(str(e))
