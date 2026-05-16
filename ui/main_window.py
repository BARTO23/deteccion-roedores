import sys
import cv2
import numpy as np
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QStatusBar, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

from core.image_loader import ImageLoader
from core.detector import ThermalDetector
from core.blob_analyzer import BlobAnalyzer
from core.projector import Projector
from utils.exporter import Exporter
from utils.logger import app_logger


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detector de Roedores - Thermal Analysis")
        self.setMinimumSize(900, 700)

        self.thermal_img: Optional[np.ndarray] = None
        self.visible_img: Optional[np.ndarray] = None
        self.result_img: Optional[np.ndarray] = None
        self.detected_points = []

        self.loader = ImageLoader()
        self.detector = ThermalDetector(threshold=0.58, background_value=-32767.0)
        self.blob_analyzer = BlobAnalyzer(min_area=1, max_area=50000)
        self.projector = Projector(circle_radius=10)

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        controls_group = QGroupBox("Controles")
        controls_layout = QHBoxLayout()

        self.btn_load_thermal = QPushButton("Cargar TIF Térmico")
        self.btn_load_thermal.clicked.connect(self._load_thermal)
        controls_layout.addWidget(self.btn_load_thermal)

        self.btn_load_visible = QPushButton("Cargar PNG Visible")
        self.btn_load_visible.clicked.connect(self._load_visible)
        controls_layout.addWidget(self.btn_load_visible)

        controls_layout.addSpacing(20)

        controls_layout.addWidget(QLabel("Umbral:"))
        self.edit_threshold = QLineEdit("0.58")
        self.edit_threshold.setFixedWidth(60)
        controls_layout.addWidget(self.edit_threshold)

        self.btn_detect = QPushButton("Detectar")
        self.btn_detect.clicked.connect(self._run_detection)
        self.btn_detect.setEnabled(False)
        controls_layout.addWidget(self.btn_detect)

        controls_layout.addStretch()

        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)

        self.lbl_preview = QLabel("Carga las imágenes para comenzar")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setMinimumSize(800, 500)
        self.lbl_preview.setStyleSheet("border: 1px solid #ccc; background: #f5f5f5;")
        main_layout.addWidget(self.lbl_preview)

        export_group = QGroupBox("Resultados")
        export_layout = QHBoxLayout()

        self.lbl_count = QLabel("Roedores detectados: 0")
        self.lbl_count.setStyleSheet("font-weight: bold; font-size: 14px;")
        export_layout.addWidget(self.lbl_count)

        export_layout.addStretch()

        self.btn_export_img = QPushButton("Exportar Imagen")
        self.btn_export_img.clicked.connect(self._export_image)
        self.btn_export_img.setEnabled(False)
        export_layout.addWidget(self.btn_export_img)

        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_csv.clicked.connect(self._export_csv)
        self.btn_export_csv.setEnabled(False)
        export_layout.addWidget(self.btn_export_csv)

        export_group.setLayout(export_layout)
        main_layout.addWidget(export_group)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo")

    def _load_thermal(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen térmica", "", "TIFF Files (*.tif *.tiff)"
        )
        if path:
            try:
                self.thermal_img = self.loader.load_thermal(path)
                self.status_bar.showMessage(f"Thermal cargada: {Path(path).name}")
                self._check_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar: {e}")

    def _load_visible(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen visible", "", "Image Files (*.png *.jpg *.jpeg);;PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )
        if path:
            try:
                self.visible_img = self.loader.load_visible(path)
                self.status_bar.showMessage(f"Visible cargada: {Path(path).name}")
                self._check_ready()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar: {e}")

    def _check_ready(self):
        ready = self.thermal_img is not None and self.visible_img is not None
        self.btn_detect.setEnabled(ready)
        if ready:
            self.status_bar.showMessage("Ambas imágenes cargadas - listo para detectar")

    def _run_detection(self):
        if self.thermal_img is None or self.visible_img is None:
            return

        try:
            threshold = float(self.edit_threshold.text())
            self.detector.set_threshold(threshold)

            self.detected_points = self.detector.detect_matlab_style(self.thermal_img)

            self.result_img = self.projector.project(self.visible_img, self.detected_points, self.thermal_img.shape)
            self._display_image(self.result_img)

            self.lbl_count.setText(f"Roedores detectados: {len(self.detected_points)}")
            self.status_bar.showMessage(f"Detección completada: {len(self.detected_points)} roedores")

            self.btn_export_img.setEnabled(True)
            self.btn_export_csv.setEnabled(True)

        except Exception as e:
            app_logger.error(f"Error en detección: {e}")
            QMessageBox.critical(self, "Error", f"Error en detección: {e}")

    def _display_image(self, img: np.ndarray):
        if img is None:
            return

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_preview.setPixmap(scaled)

    def _export_image(self):
        if self.result_img is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagen con detecciones", "", "PNG Files (*.png)"
        )
        if path:
            Exporter.save_image(self.result_img, path)
            QMessageBox.information(self, "Éxito", "Imagen exportada correctamente")

    def _export_csv(self):
        if not self.detected_points:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar coordenadas", "", "CSV Files (*.csv)"
        )
        if path:
            metadata = {"threshold": self.edit_threshold.text()}
            Exporter.save_csv(self.detected_points, path, metadata)
            QMessageBox.information(self, "Éxito", "CSV exportado correctamente")