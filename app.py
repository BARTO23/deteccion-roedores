import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import app_logger


def main():
    app_logger.info("Iniciando aplicación detector de roedores")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    app_logger.info("Aplicación iniciada correctamente")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()