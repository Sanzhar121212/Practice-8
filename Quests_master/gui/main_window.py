from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
)

from core.database import Database
from core.template_engine import TemplateEngine
from core.gamification import XPManager
from gui.quest_wizard import QuestWizard
from gui.map_editor import MapEditor
from gui.gamification_panel import GamificationPanel


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Quest Master - Гильдия Приключенцев")
        self.resize(1200, 800)

        self.db = Database()
        self.template_engine = TemplateEngine()
        self.xp_manager = XPManager()

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()

        # Вкладка квестов
        self.quest_wizard = QuestWizard(self.db, self.template_engine, self)
        self.quest_wizard.quest_created.connect(self._on_quest_created)
        self.quest_wizard.xp_event.connect(self._on_xp_event)

        # Вкладка карты
        self.map_editor = MapEditor(self.db, self)
        self.map_editor.xp_event.connect(self._on_xp_event)

        # Вкладка геймификации
        self.gamification_panel = GamificationPanel(self)

        self.tabs.addTab(self.quest_wizard, "Квесты")
        self.tabs.addTab(self.map_editor, "Карта")
        self.tabs.addTab(self.gamification_panel, "Прогресс")

        main_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # Изначально привязываем карту к текущему квесту
        self.map_editor.set_quest(self.quest_wizard.quest_id)

    def _on_quest_created(self, quest_id: int) -> None:
        # Привязываем редактор карты к этому квесту
        self.map_editor.set_quest(quest_id)

    def _on_xp_event(self, event: str) -> None:
        self.xp_manager.add_event(event)
        progress = self.xp_manager.get_progress_to_next_level()
        self.gamification_panel.update_state(self.xp_manager.state, progress)
