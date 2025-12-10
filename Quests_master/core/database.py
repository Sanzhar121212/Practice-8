from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parent.parent / "quest_master.db"


@dataclass
class Quest:
    id: int
    title: str
    difficulty: str
    reward: int
    description: str
    deadline: str
    created_at: str


class Database:
    """SQLite CRUD + версия квестов + локации."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        cur = self.conn.cursor()
        # Основные таблицы из задания
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                difficulty TEXT CHECK(difficulty IN ('Легкий','Средний','Сложный','Эпический')),
                reward INTEGER,
                description TEXT,
                deadline TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quest_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quest_id INTEGER,
                title TEXT,
                difficulty TEXT,
                reward INTEGER,
                description TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            );
            """
        )
        # Доп. таблица для локаций карты (привязка к квесту)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS quest_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quest_id INTEGER NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                kind TEXT NOT NULL, -- city, lair, tavern
                label TEXT,
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            );
            """
        )
        self.conn.commit()

    # ---------- Работа с квестами ----------

    def create_draft_quest(self) -> int:
        """Создаём «черновой» квест, чтобы сразу автосохранять поля."""
        cur = self.conn.cursor()

        # Считаем, сколько уже есть «Новый квест%»
        cur.execute(
            "SELECT COUNT(*) FROM quests WHERE title LIKE 'Новый квест%'"
        )
        count = cur.fetchone()[0]

        if count == 0:
            title = "Новый квест"
        else:
            title = f"Новый квест #{count + 1}"

        cur.execute(
            """
            INSERT INTO quests (title, difficulty, reward, description, deadline)
            VALUES (?, 'Легкий', ?, '', '')
            """,
            (title, 10),
        )
        quest_id = cur.lastrowid
        self.conn.commit()
        self._snapshot_version(quest_id)
        return quest_id

    def _snapshot_version(self, quest_id: int) -> None:
        """Сохраняем версию квеста в quest_versions."""
        quest = self.get_quest(quest_id)
        if quest is None:
            return
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO quest_versions (quest_id, title, difficulty, reward, description, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (quest.id, quest.title, quest.difficulty, quest.reward, quest.description),
        )
        self.conn.commit()

    def update_quest_field(self, quest_id: int, field: str, value: Any) -> None:
        """Автосохранение: UPDATE quests + INSERT INTO quest_versions."""
        if field not in {"title", "difficulty", "reward", "description", "deadline"}:
            raise ValueError(f"Unknown quest field: {field}")

        cur = self.conn.cursor()
        cur.execute(f"UPDATE quests SET {field} = ? WHERE id = ?", (value, quest_id))
        self.conn.commit()
        self._snapshot_version(quest_id)

    def get_quest(self, quest_id: int) -> Optional[Quest]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM quests WHERE id = ?", (quest_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return Quest(
            id=row["id"],
            title=row["title"],
            difficulty=row["difficulty"],
            reward=row["reward"],
            description=row["description"],
            deadline=row["deadline"],
            created_at=row["created_at"],
        )

    def get_quest_as_dict(self, quest_id: int) -> Optional[Dict[str, Any]]:
        quest = self.get_quest(quest_id)
        if quest is None:
            return None
        return quest.__dict__.copy()

    # ---------- Локации карты ----------

    def add_location(
        self,
        quest_id: int,
        x: float,
        y: float,
        kind: str,
        label: str = "",
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO quest_locations (quest_id, x, y, kind, label)
            VALUES (?, ?, ?, ?, ?)
            """,
            (quest_id, x, y, kind, label),
        )
        self.conn.commit()

    def get_locations_for_quest(self, quest_id: int) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, x, y, kind, label FROM quest_locations WHERE quest_id = ?",
            (quest_id,),
        )
        return [dict(row) for row in cur.fetchall()]
