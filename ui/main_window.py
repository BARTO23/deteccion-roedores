import cv2
import numpy as np
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFileDialog, QStatusBar, QMessageBox,
    QFrame, QSlider, QDoubleSpinBox, QStackedWidget, QButtonGroup,
    QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent

from core.image_loader import ImageLoader
from core.detector import ThermalDetector
from core.projector import Projector
from ui.worker import DetectionWorker
from ui.styles import STYLESHEET
from utils.exporter import Exporter
from utils.logger import app_logger

THERMAL_EXTS = {".tif", ".tiff"}
VISIBLE_EXTS = {".png", ".jpg", ".jpeg"}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detector de Roedores — Análisis Térmico")
        self.setMinimumSize(1180, 740)
        self.setStyleSheet(STYLESHEET)
        self.setAcceptDrops(True)

        self.thermal_img: Optional[np.ndarray] = None
        self.visible_img: Optional[np.ndarray] = None
        self.result_img: Optional[np.ndarray] = None
        self.detected_points = []
        self.detection_thread: Optional[DetectionWorker] = None

        self._thermal_pixmap: Optional[QPixmap] = None
        self._visible_pixmap: Optional[QPixmap] = None
        self._result_pixmap: Optional[QPixmap] = None

        self.loader = ImageLoader()
        self.detector = ThermalDetector(threshold=0.58, background_value=-32767.0)
        self.projector = Projector(circle_radius=10)

        self._init_ui()

    # ------------------------------------------------------------------ UI

    def _init_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._build_topbar())
        right_layout.addWidget(self._build_content(), 1)
        root.addWidget(right, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo — cargá las dos imágenes para comenzar")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(300)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Detector de Roedores")
        title.setObjectName("appTitle")
        subtitle = QLabel("Análisis térmico de cultivos")
        subtitle.setObjectName("appSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._divider())

        # Paso 1 — imágenes
        layout.addWidget(self._section_label("PASO 1 · IMÁGENES"))

        self.btn_load_thermal = QPushButton("Cargar imagen térmica (.tif)")
        self.btn_load_thermal.setObjectName("sidebarButton")
        self.btn_load_thermal.clicked.connect(self._pick_thermal)
        layout.addWidget(self.btn_load_thermal)
        self.lbl_thermal_status = QLabel("○ Pendiente")
        self.lbl_thermal_status.setObjectName("fileStatusPending")
        layout.addWidget(self.lbl_thermal_status)

        self.btn_load_visible = QPushButton("Cargar imagen visible (.png/.jpg)")
        self.btn_load_visible.setObjectName("sidebarButton")
        self.btn_load_visible.clicked.connect(self._pick_visible)
        layout.addWidget(self.btn_load_visible)
        self.lbl_visible_status = QLabel("○ Pendiente")
        self.lbl_visible_status.setObjectName("fileStatusPending")
        layout.addWidget(self.lbl_visible_status)

        layout.addWidget(self._divider())

        # Paso 2 — umbral
        layout.addWidget(self._section_label("PASO 2 · UMBRAL DE SENSIBILIDAD"))

        threshold_row = QHBoxLayout()
        self.slider_threshold = QSlider(Qt.Horizontal)
        self.slider_threshold.setObjectName("thresholdSlider")
        self.slider_threshold.setRange(0, 100)
        self.slider_threshold.setValue(58)
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setObjectName("thresholdSpin")
        self.spin_threshold.setRange(0.0, 1.0)
        self.spin_threshold.setSingleStep(0.01)
        self.spin_threshold.setDecimals(2)
        self.spin_threshold.setValue(0.58)
        self.spin_threshold.setFixedWidth(64)
        self.slider_threshold.valueChanged.connect(self._on_slider_changed)
        self.spin_threshold.valueChanged.connect(self._on_spin_changed)
        threshold_row.addWidget(self.slider_threshold, 1)
        threshold_row.addWidget(self.spin_threshold)
        layout.addLayout(threshold_row)

        hint = QLabel("Menor umbral = más detecciones. Recomendado: 0.58")
        hint.setObjectName("fileStatusPending")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addWidget(self._divider())

        # Paso 3 — detectar
        layout.addWidget(self._section_label("PASO 3 · DETECCIÓN"))

        self.btn_detect = QPushButton("Ejecutar Detección")
        self.btn_detect.setObjectName("primaryButton")
        self.btn_detect.clicked.connect(self._run_detection)
        self.btn_detect.setEnabled(False)
        layout.addWidget(self.btn_detect)

        self.progress = QProgressBar()
        self.progress.setObjectName("detectProgress")
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        layout.addWidget(self._divider())

        # Paso 4 — resultados
        layout.addWidget(self._section_label("RESULTADOS"))

        kpi = QFrame()
        kpi.setObjectName("kpiCard")
        kpi_layout = QVBoxLayout(kpi)
        kpi_layout.setContentsMargins(14, 12, 14, 12)
        self.lbl_kpi_value = QLabel("0")
        self.lbl_kpi_value.setObjectName("kpiValue")
        self.lbl_kpi_value.setAlignment(Qt.AlignCenter)
        lbl_kpi_caption = QLabel("roedores detectados")
        lbl_kpi_caption.setObjectName("kpiLabel")
        lbl_kpi_caption.setAlignment(Qt.AlignCenter)
        kpi_layout.addWidget(self.lbl_kpi_value)
        kpi_layout.addWidget(lbl_kpi_caption)
        layout.addWidget(kpi)

        export_row = QHBoxLayout()
        self.btn_export_img = QPushButton("Exportar imagen")
        self.btn_export_img.setObjectName("exportButton")
        self.btn_export_img.clicked.connect(self._export_image)
        self.btn_export_img.setEnabled(False)
        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_csv.setObjectName("exportButton")
        self.btn_export_csv.clicked.connect(self._export_csv)
        self.btn_export_csv.setEnabled(False)
        export_row.addWidget(self.btn_export_img)
        export_row.addWidget(self.btn_export_csv)
        layout.addLayout(export_row)

        layout.addStretch()
        return sidebar

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topBar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 8, 24, 8)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        self.lbl_topbar_title = QLabel("Vista previa")
        self.lbl_topbar_title.setObjectName("topBarTitle")
        self.lbl_topbar_hint = QLabel("Arrastrá archivos aquí o usá los botones de la izquierda")
        self.lbl_topbar_hint.setObjectName("topBarHint")
        text_col.addWidget(self.lbl_topbar_title)
        text_col.addWidget(self.lbl_topbar_hint)
        layout.addLayout(text_col)
        layout.addStretch()

        self.btn_view_input = QPushButton("Entrada")
        self.btn_view_input.setObjectName("viewToggle")
        self.btn_view_input.setCheckable(True)
        self.btn_view_input.setChecked(True)
        self.btn_view_result = QPushButton("Resultado")
        self.btn_view_result.setObjectName("viewToggle")
        self.btn_view_result.setCheckable(True)

        self.view_group = QButtonGroup(self)
        self.view_group.setExclusive(True)
        self.view_group.addButton(self.btn_view_input, 0)
        self.view_group.addButton(self.btn_view_result, 1)
        self.view_group.idClicked.connect(self._on_view_toggled)

        layout.addWidget(self.btn_view_input)
        layout.addWidget(self.btn_view_result)
        return bar

    def _build_content(self) -> QWidget:
        self.stack = QStackedWidget()

        # Página 0: entrada (térmica + visible lado a lado)
        input_page = QWidget()
        input_layout = QGridLayout(input_page)
        input_layout.setContentsMargins(24, 20, 24, 20)
        input_layout.setSpacing(12)

        cap_thermal = QLabel("IMAGEN TÉRMICA")
        cap_thermal.setObjectName("previewCaption")
        cap_visible = QLabel("IMAGEN VISIBLE")
        cap_visible.setObjectName("previewCaption")

        self.lbl_preview_thermal = QLabel("Sin imagen cargada")
        self.lbl_preview_thermal.setObjectName("previewLabel")
        self.lbl_preview_thermal.setAlignment(Qt.AlignCenter)
        self.lbl_preview_thermal.setMinimumSize(300, 300)
        self.lbl_preview_thermal.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.lbl_preview_visible = QLabel("Sin imagen cargada")
        self.lbl_preview_visible.setObjectName("previewLabel")
        self.lbl_preview_visible.setAlignment(Qt.AlignCenter)
        self.lbl_preview_visible.setMinimumSize(300, 300)
        self.lbl_preview_visible.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        input_layout.addWidget(cap_thermal, 0, 0)
        input_layout.addWidget(cap_visible, 0, 1)
        input_layout.addWidget(self.lbl_preview_thermal, 1, 0)
        input_layout.addWidget(self.lbl_preview_visible, 1, 1)

        # Página 1: resultado
        result_page = QWidget()
        result_layout = QVBoxLayout(result_page)
        result_layout.setContentsMargins(24, 20, 24, 20)
        self.lbl_preview_result = QLabel("Ejecutá la detección para ver el resultado")
        self.lbl_preview_result.setObjectName("previewLabel")
        self.lbl_preview_result.setAlignment(Qt.AlignCenter)
        self.lbl_preview_result.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        result_layout.addWidget(self.lbl_preview_result)

        self.stack.addWidget(input_page)
        self.stack.addWidget(result_page)
        return self.stack

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setObjectName("sidebarDivider")
        line.setFrameShape(QFrame.HLine)
        return line

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("stepLabel")
        return lbl

    # ------------------------------------------------------------ Drag&drop

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = Path(path).suffix.lower()
            if ext in THERMAL_EXTS:
                self._load_thermal_path(path)
            elif ext in VISIBLE_EXTS:
                self._load_visible_path(path)
            else:
                self.status_bar.showMessage(f"Formato no reconocido: {Path(path).name}")

    # ------------------------------------------------------------- Umbral

    def _on_slider_changed(self, value: int):
        self.spin_threshold.blockSignals(True)
        self.spin_threshold.setValue(value / 100.0)
        self.spin_threshold.blockSignals(False)

    def _on_spin_changed(self, value: float):
        self.slider_threshold.blockSignals(True)
        self.slider_threshold.setValue(round(value * 100))
        self.slider_threshold.blockSignals(False)

    def _on_view_toggled(self, view_id: int):
        self.stack.setCurrentIndex(view_id)
        self.lbl_topbar_title.setText("Vista previa" if view_id == 0 else "Resultado de detección")

    # --------------------------------------------------------------- Carga

    def _pick_thermal(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen térmica", "", "TIFF Files (*.tif *.tiff)"
        )
        if path:
            self._load_thermal_path(path)

    def _pick_visible(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen visible", "",
            "Image Files (*.png *.jpg *.jpeg);;PNG Files (*.png);;JPEG Files (*.jpg *.jpeg)"
        )
        if path:
            self._load_visible_path(path)

    def _load_thermal_path(self, path: str):
        try:
            self.thermal_img = self.loader.load_thermal(path)
            self._refresh_status_style(self.lbl_thermal_status, ok=True, text=f"✓ {Path(path).name}")
            self._show_thermal_preview()
            self.status_bar.showMessage(f"Térmica cargada: {Path(path).name}")
            self._check_ready()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen térmica:\n{e}")

    def _load_visible_path(self, path: str):
        try:
            self.visible_img = self.loader.load_visible(path)
            self._refresh_status_style(self.lbl_visible_status, ok=True, text=f"✓ {Path(path).name}")
            self._show_visible_preview()
            self.status_bar.showMessage(f"Visible cargada: {Path(path).name}")
            self._check_ready()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen visible:\n{e}")

    def _refresh_status_style(self, label: QLabel, ok: bool, text: Optional[str] = None):
        if text is not None:
            label.setText(text)
        label.setObjectName("fileStatusOk" if ok else "fileStatusPending")
        label.style().unpolish(label)
        label.style().polish(label)

    def _check_ready(self):
        ready = self.thermal_img is not None and self.visible_img is not None
        self.btn_detect.setEnabled(ready)
        if ready:
            self.status_bar.showMessage("Ambas imágenes cargadas — listo para detectar")

    # --------------------------------------------------------- Previsualización

    def _show_thermal_preview(self):
        normalized = ImageLoader.normalize_thermal(self.thermal_img)
        colored = cv2.applyColorMap((normalized * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
        rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
        self._thermal_pixmap = self._to_pixmap(rgb)
        self._render_pixmap(self.lbl_preview_thermal, self._thermal_pixmap)

    def _show_visible_preview(self):
        rgb = cv2.cvtColor(self.visible_img, cv2.COLOR_BGR2RGB)
        self._visible_pixmap = self._to_pixmap(rgb)
        self._render_pixmap(self.lbl_preview_visible, self._visible_pixmap)

    @staticmethod
    def _to_pixmap(rgb: np.ndarray) -> QPixmap:
        rgb = np.ascontiguousarray(rgb)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())

    @staticmethod
    def _render_pixmap(label: QLabel, pixmap: QPixmap):
        if pixmap is None or pixmap.isNull():
            return
        scaled = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_pixmap(self.lbl_preview_thermal, self._thermal_pixmap)
        self._render_pixmap(self.lbl_preview_visible, self._visible_pixmap)
        self._render_pixmap(self.lbl_preview_result, self._result_pixmap)

    # ---------------------------------------------------------------- Detección

    def _run_detection(self):
        if self.thermal_img is None or self.visible_img is None:
            return

        threshold = self.spin_threshold.value()
        self._set_busy(True)

        self.detection_thread = DetectionWorker(
            self.detector, self.projector, self.thermal_img, self.visible_img, threshold
        )
        self.detection_thread.finished_ok.connect(self._on_detection_done)
        self.detection_thread.failed.connect(self._on_detection_failed)
        self.detection_thread.finished.connect(lambda: self._set_busy(False))
        self.detection_thread.start()

    def _set_busy(self, busy: bool):
        self.progress.setVisible(busy)
        self.btn_detect.setEnabled(not busy)
        self.btn_load_thermal.setEnabled(not busy)
        self.btn_load_visible.setEnabled(not busy)
        self.status_bar.showMessage("Detectando roedores..." if busy else "Listo")

    def _on_detection_done(self, points, result_img):
        self.detected_points = points
        self.result_img = result_img

        rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        self._result_pixmap = self._to_pixmap(rgb)
        self._render_pixmap(self.lbl_preview_result, self._result_pixmap)

        self.lbl_kpi_value.setText(str(len(points)))
        self.status_bar.showMessage(f"Detección completada: {len(points)} roedores detectados")

        self.btn_export_img.setEnabled(True)
        self.btn_export_csv.setEnabled(True)

        self.btn_view_result.setChecked(True)
        self._on_view_toggled(1)

    def _on_detection_failed(self, message: str):
        app_logger.error(f"Error en detección: {message}")
        QMessageBox.critical(self, "Error", f"Error en detección:\n{message}")

    # ---------------------------------------------------------------- Exportar

    def _export_image(self):
        if self.result_img is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagen con detecciones", "", "PNG Files (*.png)"
        )
        if path:
            Exporter.save_image(self.result_img, path)
            self.status_bar.showMessage(f"Imagen exportada: {Path(path).name}")

    def _export_csv(self):
        if not self.detected_points:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar coordenadas", "", "CSV Files (*.csv)"
        )
        if path:
            metadata = {"threshold": self.spin_threshold.value()}
            Exporter.save_csv(self.detected_points, path, metadata)
            self.status_bar.showMessage(f"CSV exportado: {Path(path).name}")
