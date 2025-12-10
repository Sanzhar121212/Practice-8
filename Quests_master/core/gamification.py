from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


LEVELS: Dict[str, int] = {
    "Ученик": 0,
    "Мастер пергаментов": 50,
    "Архимаг документов": 100,
}

EVENT_XP: Dict[str, int] = {
    "create_quest": 3,
    "export": 2,
    "save_map": 5,
    "boss_fight": 20,
}


@dataclass
class XPState:
    xp: int = 0
    level: str = "Ученик"
    achievements: List[str] = field(default_factory=list)


class XPManager:
    def __init__(self) -> None:
        self.state = XPState()

    def _recalculate_level(self) -> None:
        level = "Ученик"
        for name, threshold in LEVELS.items():
            if self.state.xp >= threshold:
                level = name
        self.state.level = level

    def add_event(self, event: str) -> Tuple[int, str]:
        """Добавляет XP за событие, возвращает (новый_xp, уровень)."""
        delta = EVENT_XP.get(event, 0)
        self.state.xp += delta
        self._recalculate_level()
        if delta > 0:
            self.state.achievements.append(f"+{delta} XP: {event}")
        return self.state.xp, self.state.level

    def get_progress_to_next_level(self) -> int:
        """Процент заполнения для QProgressBar."""
        current_xp = self.state.xp
        thresholds = sorted(LEVELS.values())
        next_threshold = thresholds[-1]
        for t in thresholds:
            if t > current_xp:
                next_threshold = t
                break
        prev_threshold = 0
        for t in thresholds:
            if t <= current_xp:
                prev_threshold = t
        span = max(1, next_threshold - prev_threshold)
        return int((current_xp - prev_threshold) / span * 100)
