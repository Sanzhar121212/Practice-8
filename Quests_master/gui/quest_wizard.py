from __future__ import annotations

import re
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QDateTimeEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QHBoxLayout,
    QFileDialog,
)

from core.database import Database
from core.template_engine import TemplateEngine
from pathlib import Path


class QuestWizard(QWidget):
    quest_created = pyqtSignal(int)
    xp_event = pyqtSignal(str)  # "create_quest" / "export"

    def __init__(
        self,
        db: Database,
        template_engine: TemplateEngine,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.template_engine = template_engine

        self.quest_id: int = self.db.create_draft_quest()

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setMaxLength(50)
        form_layout.addRow("Название квеста:", self.title_edit)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(
            ["Легкий", "Средний", "Сложный", "Эпический"]
        )
        form_layout.addRow("Сложность:", self.difficulty_combo)

        self.reward_spin = QSpinBox()
        self.reward_spin.setRange(10, 10000)
        form_layout.addRow("Награда (золото):", self.reward_spin)

        self.description_edit = QTextEdit()
        self.counter_label = QLabel("Символов: 0 | Слов: 0 (мин. 50 слов)")
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(self.description_edit)
        desc_layout.addWidget(self.counter_label)
        form_layout.addRow("Описание:", desc_layout)

        self.deadline_edit = QDateTimeEdit()
        self.deadline_edit.setDateTime(QDateTime.currentDateTime())
        self.deadline_edit.setCalendarPopup(True)
        form_layout.addRow("Дедлайн:", self.deadline_edit)

        main_layout.addLayout(form_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.create_button = QPushButton("Создать квест")
        self.export_pdf_button = QPushButton("Экспорт в PDF")
        self.export_docx_button = QPushButton("Экспорт в DOCX")
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.export_pdf_button)
        buttons_layout.addWidget(self.export_docx_button)
        main_layout.addLayout(buttons_layout)

        # Горячая клавиша Ctrl+Enter
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self._on_create_clicked)

    def _connect_signals(self) -> None:
        self.title_edit.textChanged.connect(self._on_title_changed)
        self.difficulty_combo.currentTextChanged.connect(self._on_difficulty_changed)
        self.reward_spin.valueChanged.connect(self._on_reward_changed)
        self.description_edit.textChanged.connect(self._on_description_changed)
        self.deadline_edit.dateTimeChanged.connect(self._on_deadline_changed)

        self.create_button.clicked.connect(self._on_create_clicked)
        self.export_pdf_button.clicked.connect(self._on_export_pdf)
        self.export_docx_button.clicked.connect(self._on_export_docx)

    # ---------- Автосохранение полей ----------

    def _on_title_changed(self, text: str) -> None:
        self.db.update_quest_field(self.quest_id, "title", text)
        self._validate_fields()

    def _on_difficulty_changed(self, text: str) -> None:
        self.db.update_quest_field(self.quest_id, "difficulty", text)

    def _on_reward_changed(self, value: int) -> None:
        self.db.update_quest_field(self.quest_id, "reward", value)

    def _on_description_changed(self) -> None:
        text = self.description_edit.toPlainText()
        self.db.update_quest_field(self.quest_id, "description", text)
        self._update_counter()
        self._validate_fields()

    def _on_deadline_changed(self, dt: QDateTime) -> None:
        self.db.update_quest_field(self.quest_id, "deadline", dt.toString(Qt.DateFormat.ISODate))

    # ---------- Валидация ----------

    def _count_words(self, text: str) -> int:
        text = text.strip()
        if not text:
            return 0
        return len(re.split(r"\s+", text))

    def _update_counter(self) -> None:
        text = self.description_edit.toPlainText()
        chars = len(text)
        words = self._count_words(text)
        self.counter_label.setText(
            f"Символов: {chars} | Слов: {words} (мин. 50 слов)"
        )

    def _validate_fields(self) -> bool:
        ok = True
        # Название
        title = self.title_edit.text().strip()
        if not title:
            self.title_edit.setStyleSheet("border: 1px solid red;")
            ok = False
        else:
            self.title_edit.setStyleSheet("")
        # Описание
        words = self._count_words(self.description_edit.toPlainText())
        if words < 50:
            self.description_edit.setStyleSheet("border: 1px solid red;")
            ok = False
        else:
            self.description_edit.setStyleSheet("")
        return ok

    # ---------- Создание квеста ----------

    def _on_create_clicked(self) -> None:
        if not self._validate_fields():
            QMessageBox.warning(
                self,
                "Ошибка",
                "Нельзя создать квест без названия и описания (мин. 50 слов).",
            )
            return
        QMessageBox.information(
            self,
            "Готово",
            f"Квест #{self.quest_id} успешно создан!",
        )
        self.quest_created.emit(self.quest_id)
        self.xp_event.emit("create_quest")

    # ---------- Экспорт ----------

    def _export(self, kind: str) -> None:
        quest = self.db.get_quest_as_dict(self.quest_id)
        if quest is None:
            QMessageBox.warning(self, "Ошибка", "Квест не найден.")
            return

        render_result = self.template_engine.render(quest, "guild_contract.html")

        if kind == "pdf":
            default_path = self.template_engine.default_output_path(self.quest_id, "pdf")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить PDF",
                str(default_path),
                "PDF Files (*.pdf)",
            )
            if not file_path:
                return
            self.template_engine.export_pdf(render_result, Path(file_path))
        else:
            default_path = self.template_engine.default_output_path(self.quest_id, "docx")
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить DOCX",
                str(default_path),
                "Word Documents (*.docx)",
            )
            if not file_path:
                return
            self.template_engine.export_docx(quest, Path(file_path))

        QMessageBox.information(self, "Экспорт", "Экспорт успешно завершён.")
        self.xp_event.emit("export")

    def _on_export_pdf(self) -> None:
        self._export("pdf")

    def _on_export_docx(self) -> None:
        self._export("docx")
