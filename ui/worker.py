import numpy as np
from typing import List, Tuple, Optional
from PySide6.QtCore import QThread, Signal

from core.detector import ThermalDetector
from core.projector import Projector


class DetectionWorker(QThread):
    """Corre detección + proyección fuera del hilo de UI."""

    finished_ok = Signal(list, np.ndarray)
    failed = Signal(str)

    def __init__(
        self,
        detector: ThermalDetector,
        projector: Projector,
        thermal_img: np.ndarray,
        visible_img: np.ndarray,
        threshold: float,
        parent=None
    ):
        super().__init__(parent)
        self.detector = detector
        self.projector = projector
        self.thermal_img = thermal_img
        self.visible_img = visible_img
        self.threshold = threshold

    def run(self):
        try:
            self.detector.set_threshold(self.threshold)
            points: List[Tuple[int, int]] = self.detector.detect_matlab_style(self.thermal_img)
            result_img = self.projector.project(self.visible_img, points, self.thermal_img.shape)
            self.finished_ok.emit(points, result_img)
        except Exception as e:
            self.failed.emit(str(e))
