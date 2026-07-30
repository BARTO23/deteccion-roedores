"""Paleta y hoja de estilos (QSS) corporativa para la aplicación."""

COLORS = {
    "bg": "#F1F5F9",
    "surface": "#FFFFFF",
    "sidebar": "#1E293B",
    "sidebar_alt": "#273449",
    "border": "#E2E8F0",
    "text": "#0F172A",
    "text_muted": "#64748B",
    "text_on_dark": "#F8FAFC",
    "text_on_dark_muted": "#94A3B8",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_pressed": "#1E40AF",
    "success": "#16A34A",
    "success_bg": "#DCFCE7",
    "danger": "#DC2626",
    "pending": "#475569",
    "pending_bg": "#334155",
}

STYLESHEET = f"""
QMainWindow, QWidget#centralWidget {{
    background: {COLORS['bg']};
}}

QWidget#sidebar {{
    background: {COLORS['sidebar']};
}}

QScrollArea#sidebarScroll, QScrollArea#sidebarScroll > QWidget > QWidget {{
    background: {COLORS['sidebar']};
    border: none;
}}

QScrollArea#sidebarScroll QScrollBar:vertical {{
    background: {COLORS['sidebar']};
    width: 8px;
    margin: 0;
}}
QScrollArea#sidebarScroll QScrollBar::handle:vertical {{
    background: #475569;
    border-radius: 4px;
    min-height: 24px;
}}
QScrollArea#sidebarScroll QScrollBar::handle:vertical:hover {{
    background: #64748B;
}}
QScrollArea#sidebarScroll QScrollBar::add-line:vertical,
QScrollArea#sidebarScroll QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollArea#sidebarScroll QScrollBar::add-page:vertical,
QScrollArea#sidebarScroll QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QSplitter#mainSplitter::handle {{
    background: {COLORS['border']};
}}
QSplitter#mainSplitter::handle:hover {{
    background: {COLORS['primary']};
}}

QLabel#appTitle {{
    color: {COLORS['text_on_dark']};
    font-size: 16px;
    font-weight: 600;
}}

QLabel#appSubtitle {{
    color: {COLORS['text_on_dark_muted']};
    font-size: 11px;
}}

QLabel#stepLabel {{
    color: {COLORS['text_on_dark_muted']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
}}

QLabel#fileStatusPending {{
    color: {COLORS['text_on_dark_muted']};
    font-size: 11px;
}}

QLabel#fileStatusOk {{
    color: {COLORS['success']};
    font-size: 11px;
    font-weight: 600;
}}

QFrame#sidebarDivider {{
    background: {COLORS['sidebar_alt']};
    max-height: 1px;
}}

QPushButton#sidebarButton {{
    background: {COLORS['sidebar_alt']};
    color: {COLORS['text_on_dark']};
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 9px 12px;
    text-align: left;
    font-size: 12px;
}}
QPushButton#sidebarButton:hover {{
    background: #334155;
}}
QPushButton#sidebarButton:disabled {{
    color: {COLORS['text_on_dark_muted']};
    background: {COLORS['sidebar_alt']};
}}

QPushButton#primaryButton {{
    background: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 11px 12px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background: {COLORS['primary_hover']};
}}
QPushButton#primaryButton:pressed {{
    background: {COLORS['primary_pressed']};
}}
QPushButton#primaryButton:disabled {{
    background: #3B4B63;
    color: {COLORS['text_on_dark_muted']};
}}

QPushButton#exportButton {{
    background: transparent;
    color: {COLORS['text_on_dark']};
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}}
QPushButton#exportButton:hover {{
    background: {COLORS['sidebar_alt']};
}}
QPushButton#exportButton:disabled {{
    color: {COLORS['text_on_dark_muted']};
    border-color: #334155;
}}

QDoubleSpinBox#thresholdSpin {{
    background: {COLORS['sidebar_alt']};
    color: {COLORS['text_on_dark']};
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
}}

QSlider#thresholdSlider::groove:horizontal {{
    height: 4px;
    background: #334155;
    border-radius: 2px;
}}
QSlider#thresholdSlider::handle:horizontal {{
    background: {COLORS['primary']};
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}}
QSlider#thresholdSlider::sub-page:horizontal {{
    background: {COLORS['primary']};
    border-radius: 2px;
}}

QCheckBox#clusterCheck {{
    color: {COLORS['text_on_dark_muted']};
    font-size: 11px;
    spacing: 6px;
}}
QCheckBox#clusterCheck::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid #475569;
    border-radius: 3px;
    background: {COLORS['sidebar_alt']};
}}
QCheckBox#clusterCheck::indicator:checked {{
    background: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

QSpinBox#thresholdSpin {{
    background: {COLORS['sidebar_alt']};
    color: {COLORS['text_on_dark']};
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
}}

QFrame#kpiCard {{
    background: {COLORS['sidebar_alt']};
    border-radius: 8px;
    border: 1px solid #334155;
}}

QLabel#kpiValue {{
    color: {COLORS['text_on_dark']};
    font-size: 28px;
    font-weight: 700;
}}

QLabel#kpiLabel {{
    color: {COLORS['text_on_dark_muted']};
    font-size: 11px;
}}

QWidget#topBar {{
    background: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
}}

QLabel#topBarTitle {{
    color: {COLORS['text']};
    font-size: 14px;
    font-weight: 600;
}}

QLabel#topBarHint {{
    color: {COLORS['text_muted']};
    font-size: 11px;
}}

QPushButton#viewToggle {{
    background: transparent;
    color: {COLORS['text_muted']};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 4px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#viewToggle:checked {{
    color: {COLORS['primary']};
    border-bottom: 2px solid {COLORS['primary']};
}}
QPushButton#viewToggle:hover {{
    color: {COLORS['primary_hover']};
}}

QLabel#previewLabel {{
    background: {COLORS['surface']};
    border: 1px dashed {COLORS['border']};
    border-radius: 8px;
    color: {COLORS['text_muted']};
    font-size: 12px;
}}

QLabel#previewCaption {{
    color: {COLORS['text_muted']};
    font-size: 11px;
    font-weight: 600;
}}

QStatusBar {{
    background: {COLORS['surface']};
    border-top: 1px solid {COLORS['border']};
    color: {COLORS['text_muted']};
    font-size: 11px;
}}

QProgressBar#detectProgress {{
    background: #334155;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar#detectProgress::chunk {{
    background: {COLORS['primary']};
    border-radius: 3px;
}}
"""
