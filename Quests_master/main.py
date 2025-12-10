import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase

from gui.main_window import MainWindow


def load_custom_fonts() -> None:
    """Подключаем Uncial Antiqua из assets/fonts."""
    fonts_dir = Path(__file__).parent / "assets" / "fonts"
    font_file = fonts_dir / "UncialAntiqua-Regular.ttf"
    if font_file.exists():
        QFontDatabase.addApplicationFont(str(font_file))


def main() -> None:
    app = QApplication(sys.argv)
    load_custom_fonts()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
