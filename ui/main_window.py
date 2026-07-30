import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFileDialog, QStatusBar, QMessageBox,
    QFrame, QSlider, QDoubleSpinBox, QStackedWidget, QButtonGroup,
    QProgressBar, QSizePolicy, QCheckBox, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent

from core.image_loader import ImageLoader
from core.detector import ThermalDetector, MATLAB_THRESHOLD
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
        self.setMinimumSize(860, 560)
        self.resize(1280, 800)
        self.setStyleSheet(STYLESHEET)
        self.setAcceptDrops(True)

        self.thermal_img: Optional[np.ndarray] = None
        self.visible_img: Optional[np.ndarray] = None
        self.result_img: Optional[np.ndarray] = None
        self.detected_points = []
        self.pixel_count = 0
        self.detection_thread: Optional[DetectionWorker] = None

        self._thermal_pixmap: Optional[QPixmap] = None
        self._visible_pixmap: Optional[QPixmap] = None
        self._result_pixmap: Optional[QPixmap] = None
        self._preview_columns = 2

        self.loader = ImageLoader()
        self.detector = ThermalDetector()
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

        # El panel de controles va dentro de un scroll: en ventanas bajas los
        # pasos siguen siendo alcanzables en vez de quedar recortados.
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setObjectName("sidebarScroll")
        self.sidebar_scroll.setWidget(self._build_sidebar())
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setFrameShape(QFrame.NoFrame)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar_scroll.setMinimumWidth(268)
        self.sidebar_scroll.setMaximumWidth(420)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._build_topbar())
        right_layout.addWidget(self._build_content(), 1)

        # Splitter para que el usuario ajuste el ancho del panel a su pantalla.
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("mainSplitter")
        self.splitter.setHandleWidth(1)
        self.splitter.addWidget(self.sidebar_scroll)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setSizes([300, 980])
        # Arrastrar el divisor cambia el ancho del contenido sin resize de ventana.
        self.splitter.splitterMoved.connect(lambda *_: self._on_content_resized())
        root.addWidget(self.splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo — cargá las dos imágenes para comenzar")

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Detector de Roedores")
        title.setObjectName("appTitle")
        title.setWordWrap(True)
        subtitle = QLabel("Análisis térmico de cultivos")
        subtitle.setObjectName("appSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._divider())

        # Paso 1 — imágenes
        layout.addWidget(self._section_label("PASO 1 · IMÁGENES"))

        self.btn_load_thermal = QPushButton("Cargar térmica (.tif)")
        self.btn_load_thermal.setObjectName("sidebarButton")
        self.btn_load_thermal.setToolTip("Seleccionar la imagen térmica .tif del vuelo")
        self.btn_load_thermal.clicked.connect(self._pick_thermal)
        layout.addWidget(self.btn_load_thermal)
        self.lbl_thermal_status = QLabel("○ Pendiente")
        self.lbl_thermal_status.setObjectName("fileStatusPending")
        self.lbl_thermal_status.setWordWrap(True)
        layout.addWidget(self.lbl_thermal_status)

        self.btn_load_visible = QPushButton("Cargar visible (.png/.jpg)")
        self.btn_load_visible.setObjectName("sidebarButton")
        self.btn_load_visible.setToolTip("Seleccionar la foto del dron del mismo lote")
        self.btn_load_visible.clicked.connect(self._pick_visible)
        layout.addWidget(self.btn_load_visible)
        self.lbl_visible_status = QLabel("○ Pendiente")
        self.lbl_visible_status.setObjectName("fileStatusPending")
        self.lbl_visible_status.setWordWrap(True)
        layout.addWidget(self.lbl_visible_status)

        layout.addWidget(self._divider())

        # Paso 2 — umbral
        layout.addWidget(self._section_label("PASO 2 · UMBRAL"))

        threshold_row = QHBoxLayout()
        self.slider_threshold = QSlider(Qt.Horizontal)
        self.slider_threshold.setObjectName("thresholdSlider")
        self.slider_threshold.setRange(0, 200)
        self.slider_threshold.setValue(int(MATLAB_THRESHOLD * 100))
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setObjectName("thresholdSpin")
        self.spin_threshold.setRange(0.0, 2.0)
        self.spin_threshold.setSingleStep(0.01)
        self.spin_threshold.setDecimals(2)
        self.spin_threshold.setValue(MATLAB_THRESHOLD)
        self.spin_threshold.setFixedWidth(64)
        self.slider_threshold.valueChanged.connect(self._on_slider_changed)
        self.spin_threshold.valueChanged.connect(self._on_spin_changed)
        threshold_row.addWidget(self.slider_threshold, 1)
        threshold_row.addWidget(self.spin_threshold)
        layout.addLayout(threshold_row)

        hint = QLabel(
            "Delta mínimo de temperatura contra los vecinos. "
            "Menor umbral = más detecciones. Original MATLAB: 0.56"
        )
        hint.setObjectName("fileStatusPending")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.chk_cluster = QCheckBox("Agrupar pixeles contiguos")
        self.chk_cluster.setObjectName("clusterCheck")
        self.chk_cluster.setToolTip(
            "Cuenta como un solo roedor los pixeles contiguos que disparan juntos.\n"
            "El script MATLAB original contaba cada pixel por separado."
        )
        self.chk_cluster.setChecked(False)
        layout.addWidget(self.chk_cluster)

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
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
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
        lbl_kpi_caption.setWordWrap(True)
        self.lbl_kpi_detail = QLabel("sin analizar")
        self.lbl_kpi_detail.setObjectName("kpiLabel")
        self.lbl_kpi_detail.setAlignment(Qt.AlignCenter)
        self.lbl_kpi_detail.setWordWrap(True)
        kpi_layout.addWidget(self.lbl_kpi_value)
        kpi_layout.addWidget(lbl_kpi_caption)
        kpi_layout.addWidget(self.lbl_kpi_detail)
        layout.addWidget(kpi)

        # Apilados: dos botones en fila obligaban al panel a un mínimo de ~436 px
        # y recortaban el contenido en ventanas angostas.
        self.btn_export_img = QPushButton("Exportar imagen")
        self.btn_export_img.setObjectName("exportButton")
        self.btn_export_img.clicked.connect(self._export_image)
        self.btn_export_img.setEnabled(False)
        self.btn_export_csv = QPushButton("Exportar CSV")
        self.btn_export_csv.setObjectName("exportButton")
        self.btn_export_csv.clicked.connect(self._export_csv)
        self.btn_export_csv.setEnabled(False)
        layout.addWidget(self.btn_export_img)
        layout.addWidget(self.btn_export_csv)

        # Los botones traen política Minimum: su sizeHint (el ancho del texto) pasa
        # a ser el mínimo del panel y el scroll termina recortando. Con Ignored el
        # ancho lo manda el panel y el texto se elide solo.
        for widget in (self.btn_load_thermal, self.btn_load_visible, self.btn_detect,
                       self.chk_cluster, self.btn_export_img, self.btn_export_csv):
            widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        layout.addStretch()
        return sidebar

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topBar")
        bar.setMinimumHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(8)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        self.lbl_topbar_title = QLabel("Vista previa")
        self.lbl_topbar_title.setObjectName("topBarTitle")
        self.lbl_topbar_hint = QLabel("Arrastrá archivos aquí o usá los botones de la izquierda")
        self.lbl_topbar_hint.setObjectName("topBarHint")
        # Que el texto ceda espacio antes que los botones al angostar la ventana.
        self.lbl_topbar_title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.lbl_topbar_hint.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        text_col.addWidget(self.lbl_topbar_title)
        text_col.addWidget(self.lbl_topbar_hint)
        layout.addLayout(text_col, 1)

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

        # Página 0: entrada (térmica + visible, en 2 columnas o apiladas)
        input_page = QWidget()
        self.input_grid = QGridLayout(input_page)
        self.input_grid.setContentsMargins(20, 16, 20, 16)
        self.input_grid.setSpacing(12)

        self.lbl_preview_thermal = self._make_preview_label()
        self.lbl_preview_visible = self._make_preview_label()
        self.card_thermal = self._make_preview_card("IMAGEN TÉRMICA", self.lbl_preview_thermal)
        self.card_visible = self._make_preview_card("IMAGEN VISIBLE", self.lbl_preview_visible)

        self._apply_preview_columns(2)

        # Página 1: resultado
        result_page = QWidget()
        result_layout = QVBoxLayout(result_page)
        result_layout.setContentsMargins(20, 16, 20, 16)
        self.lbl_preview_result = self._make_preview_label(
            "Ejecutá la detección para ver el resultado"
        )
        result_layout.addWidget(self.lbl_preview_result)

        self.stack.addWidget(input_page)
        self.stack.addWidget(result_page)
        return self.stack

    @staticmethod
    def _make_preview_label(text: str = "Sin imagen cargada") -> QLabel:
        label = QLabel(text)
        label.setObjectName("previewLabel")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        # Mínimo chico a propósito: el panel debe poder achicarse con la ventana.
        label.setMinimumSize(140, 120)
        label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        return label

    @staticmethod
    def _make_preview_card(caption: str, preview: QLabel) -> QWidget:
        card = QWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        lbl_caption = QLabel(caption)
        lbl_caption.setObjectName("previewCaption")
        layout.addWidget(lbl_caption)
        layout.addWidget(preview, 1)
        return card

    def _apply_preview_columns(self, columns: int):
        """Coloca las dos tarjetas lado a lado o apiladas."""
        self.input_grid.removeWidget(self.card_thermal)
        self.input_grid.removeWidget(self.card_visible)

        if columns == 2:
            self.input_grid.addWidget(self.card_thermal, 0, 0)
            self.input_grid.addWidget(self.card_visible, 0, 1)
            self.input_grid.setColumnStretch(0, 1)
            self.input_grid.setColumnStretch(1, 1)
            self.input_grid.setRowStretch(0, 1)
            self.input_grid.setRowStretch(1, 0)
        else:
            self.input_grid.addWidget(self.card_thermal, 0, 0)
            self.input_grid.addWidget(self.card_visible, 1, 0)
            self.input_grid.setColumnStretch(0, 1)
            self.input_grid.setColumnStretch(1, 0)
            self.input_grid.setRowStretch(0, 1)
            self.input_grid.setRowStretch(1, 1)

        self._preview_columns = columns

    def _reflow_previews(self):
        """Apila las previews cuando el área de contenido queda angosta."""
        width = self.stack.width()
        columns = 1 if width < 620 else 2
        if columns != self._preview_columns:
            self._apply_preview_columns(columns)

        # El texto auxiliar de la barra superior sobra en ventanas chicas.
        self.lbl_topbar_hint.setVisible(self.width() >= 1000)

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
        # Sin wrap, el ancho del rótulo fijaba el mínimo de todo el panel.
        lbl.setWordWrap(True)
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

    # Lado máximo del pixmap que se guarda para mostrar. Las imágenes de vuelo
    # rondan los 10000 px: reescalar ese tamaño en cada resize traba la ventana,
    # y en pantalla nunca se ven más de ~2000 px.
    DISPLAY_MAX_SIDE = 2000

    @classmethod
    def _to_pixmap(cls, rgb: np.ndarray) -> QPixmap:
        longest = max(rgb.shape[0], rgb.shape[1])
        if longest > cls.DISPLAY_MAX_SIDE:
            scale = cls.DISPLAY_MAX_SIDE / longest
            rgb = cv2.resize(
                rgb, (max(1, int(rgb.shape[1] * scale)), max(1, int(rgb.shape[0] * scale))),
                interpolation=cv2.INTER_AREA
            )
        rgb = np.ascontiguousarray(rgb)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())

    @staticmethod
    def _render_pixmap(label: QLabel, pixmap: QPixmap):
        if pixmap is None or pixmap.isNull():
            return
        size = label.size()
        if size.width() < 2 or size.height() < 2:
            return
        label.setPixmap(pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _render_all_previews(self):
        self._render_pixmap(self.lbl_preview_thermal, self._thermal_pixmap)
        self._render_pixmap(self.lbl_preview_visible, self._visible_pixmap)
        self._render_pixmap(self.lbl_preview_result, self._result_pixmap)

    def _on_content_resized(self):
        self._reflow_previews()
        self._render_all_previews()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._on_content_resized()

    def showEvent(self, event):
        super().showEvent(event)
        self._on_content_resized()

    # ---------------------------------------------------------------- Detección

    def _run_detection(self):
        if self.thermal_img is None or self.visible_img is None:
            return

        self._set_busy(True)

        self.detection_thread = DetectionWorker(
            self.detector,
            self.projector,
            self.thermal_img,
            self.visible_img,
            threshold=self.spin_threshold.value(),
            cluster=self.chk_cluster.isChecked(),
        )
        self.detection_thread.progress.connect(self.progress.setValue)
        self.detection_thread.stage.connect(self.status_bar.showMessage)
        self.detection_thread.finished_ok.connect(self._on_detection_done)
        self.detection_thread.failed.connect(self._on_detection_failed)
        self.detection_thread.finished.connect(lambda: self._set_busy(False))
        self.detection_thread.start()

    def _set_busy(self, busy: bool):
        if busy:
            self.progress.setValue(0)
        self.progress.setVisible(busy)
        self.btn_detect.setEnabled(not busy)
        self.btn_load_thermal.setEnabled(not busy)
        self.btn_load_visible.setEnabled(not busy)
        if busy:
            self.status_bar.showMessage("Analizando imagen térmica...")

    def _on_detection_done(self, points, pixel_count, result_img):
        self.detected_points = points
        self.pixel_count = pixel_count
        self.result_img = result_img

        rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        self._result_pixmap = self._to_pixmap(rgb)
        self._render_pixmap(self.lbl_preview_result, self._result_pixmap)

        self.lbl_kpi_value.setText(str(len(points)))
        if self.chk_cluster.isChecked() and pixel_count != len(points):
            self.lbl_kpi_detail.setText(f"{pixel_count} pixeles agrupados")
        else:
            self.lbl_kpi_detail.setText(f"T = {self.spin_threshold.value():.2f}")
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
            metadata = {
                "umbral_T": self.spin_threshold.value(),
                "vecinos_minimos": self.detector.min_neighbors,
                "delta_maximo": self.detector.max_delta,
                "agrupado": "si" if self.chk_cluster.isChecked() else "no",
                "pixeles_detectados": self.pixel_count,
                "roedores": len(self.detected_points),
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            Exporter.save_csv(self.detected_points, path, metadata)
            self.status_bar.showMessage(f"CSV exportado: {Path(path).name}")
