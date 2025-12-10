from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QListWidget

from core.gamification import XPState


class GamificationPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._init_sound()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.level_label = QLabel("Уровень: Ученик")
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.achievements_list = QListWidget()

        layout.addWidget(self.level_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("Достижения:"))
        layout.addWidget(self.achievements_list)

    def _init_sound(self) -> None:
        self.sound = QSoundEffect(self)
        # Положите любой звук в assets/icons/xp.wav или поправьте путь
        self.sound.setSource(QUrl.fromLocalFile("assets/icons/xp.wav"))
        self.sound.setVolume(0.5)

    def update_state(self, state: XPState, progress: int) -> None:
        self.level_label.setText(f"Уровень: {state.level} ({state.xp} XP)")
        self.progress_bar.setValue(progress)
        self.achievements_list.clear()
        for ach in state.achievements[-20:]:
            self.achievements_list.addItem(ach)
        self.play_xp_sound()

    def play_xp_sound(self) -> None:
        if self.sound.source().isEmpty():
            return
        self.sound.play()
