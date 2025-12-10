from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QColor, QFont, QPixmap, QAction
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QToolBar,
    QGraphicsView,
    QGraphicsScene,
    QFileDialog,
    QInputDialog,
)

from core.database import Database


BRUSH_COLOR = QColor(101, 67, 33)  # коричневый
PARCHMENT_COLOR = QColor("#f4e4bc")


class MapView(QGraphicsView):
    """Холст 800x600 с пергаментным фоном и простыми инструментами."""

    def __init__(self, db: Database, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db
        self.current_quest_id: Optional[int] = None
        self.mode: str = "brush"  # brush | city | lair | tavern | text
        self.last_pos: Optional[QPointF] = None

        scene = QGraphicsScene(self)
        self.setScene(scene)
        self.setSceneRect(0, 0, 800, 600)
        self.setBackgroundBrush(PARCHMENT_COLOR)

    @property
    def scene_obj(self) -> QGraphicsScene:
        # для удобства
        return self.scene()

    def set_quest(self, quest_id: int) -> None:
        self.current_quest_id = quest_id

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    # ---------- События мыши ----------

    def mousePressEvent(self, event) -> None:
        scene_pos = self.mapToScene(event.position().toPoint())
        self.last_pos = scene_pos

        if self.mode == "brush":
            self._draw_point(scene_pos)
        elif self.mode in {"city", "lair", "tavern"}:
            self._add_marker(scene_pos, self.mode)
        elif self.mode == "text":
            self._add_text(scene_pos)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self.mode == "brush" and self.last_pos is not None:
            new_pos = self.mapToScene(event.position().toPoint())
            pen = QPen(BRUSH_COLOR, 3)
            self.scene_obj.addLine(
                self.last_pos.x(),
                self.last_pos.y(),
                new_pos.x(),
                new_pos.y(),
                pen,
            )
            self.last_pos = new_pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.last_pos = None
        super().mouseReleaseEvent(event)

    # ---------- Инструменты ----------

    def _draw_point(self, pos: QPointF) -> None:
        pen = QPen(BRUSH_COLOR, 3)
        self.scene_obj.addEllipse(pos.x(), pos.y(), 1, 1, pen)

    def _add_marker(self, pos: QPointF, kind: str) -> None:
        if self.current_quest_id is None:
            return
        color_map = {
            "city": QColor("green"),
            "lair": QColor("red"),
            "tavern": QColor("yellow"),
        }
        color = color_map.get(kind, QColor("black"))
        pen = QPen(color)
        brush = color
        item = self.scene_obj.addEllipse(
            pos.x() - 5,
            pos.y() - 5,
            10,
            10,
            pen,
            brush,
        )
        item.setToolTip(kind)

        # Привязка локации к квесту в БД
        self.db.add_location(
            quest_id=self.current_quest_id,
            x=pos.x(),
            y=pos.y(),
            kind=kind,
            label=kind,
        )

    def _add_text(self, pos: QPointF) -> None:
        text, ok = QInputDialog.getText(self, "Метка", "Текст метки:")
        if not ok or not text:
            return
        font = QFont("Uncial Antiqua", 10)
        item = self.scene_obj.addText(text, font)
        item.setPos(pos)

    # ---------- Работа с изображением ----------

    def save_image(self) -> Optional[str]:
        """Сохранение карты в PNG/JPG."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить карту",
            "",
            "Images (*.png *.jpg)",
        )
        if not file_path:
            return None

        image = self._scene_to_image()
        image.save(file_path)
        return file_path

    def _scene_to_image(self):
        from PyQt6.QtGui import QImage, QPainter

        image = QImage(800, 600, QImage.Format.Format_ARGB32)
        image.fill(PARCHMENT_COLOR)
        painter = QPainter(image)
        self.render(painter)
        painter.end()
        return image

    def load_background(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить фон",
            "",
            "Images (*.png *.jpg *.jpeg)",
        )
        if not file_path:
            return
        pixmap = QPixmap(file_path)
        self.scene_obj.addPixmap(pixmap)


class MapEditor(QWidget):
    """Виджет-обёртка: тулбар + MapView."""
    xp_event = pyqtSignal(str)  # "save_map"

    def __init__(self, db: Database, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.db = db

        self.view = MapView(db, self)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QToolBar()
        layout.addWidget(toolbar)
        layout.addWidget(self.view)

        # Кнопки-инструменты
        brush_action = QAction("Кисть", self)
        city_action = QAction("Город", self)
        lair_action = QAction("Логово", self)
        tavern_action = QAction("Таверна", self)
        text_action = QAction("Текст", self)
        save_action = QAction("Сохранить карту", self)
        bg_action = QAction("Загрузить фон", self)

        brush_action.triggered.connect(lambda: self.view.set_mode("brush"))
        city_action.triggered.connect(lambda: self.view.set_mode("city"))
        lair_action.triggered.connect(lambda: self.view.set_mode("lair"))
        tavern_action.triggered.connect(lambda: self.view.set_mode("tavern"))
        text_action.triggered.connect(lambda: self.view.set_mode("text"))
        save_action.triggered.connect(self._on_save)
        bg_action.triggered.connect(self.view.load_background)

        for act in [
            brush_action,
            city_action,
            lair_action,
            tavern_action,
            text_action,
            save_action,
            bg_action,
        ]:
            toolbar.addAction(act)

    def set_quest(self, quest_id: int) -> None:
        """Вызывается из MainWindow, чтобы привязать карту к квесту."""
        self.view.set_quest(quest_id)

    def _on_save(self) -> None:
        path = self.view.save_image()
        if path:
            # +5 XP
            self.xp_event.emit("save_map")
