"""Player profiles, session history and progress, stored as JSON."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional

from .scoring import Report
from .zen import level_for

DEFAULT_DIR = os.environ.get("MINDZEN_HOME") or os.path.join(os.path.expanduser("~"), ".mindzen")
STORE_FILE = "profiles.json"


@dataclass
class Session:
    when: str
    index: int
    intellect: float
    clarity: float
    calm: float
    accuracy: float
    level: str
    attempts: int

    @classmethod
    def from_report(cls, report: Report) -> "Session":
        return cls(
            when=datetime.now().strftime("%Y-%m-%d %H:%M"),
            index=report.index,
            intellect=report.intellect,
            clarity=report.clarity,
            calm=report.calm,
            accuracy=report.accuracy,
            level=level_for(report.index).name,
            attempts=report.attempts,
        )


@dataclass
class Player:
    name: str
    sessions: List[Session] = field(default_factory=list)

    # ----- derived -----
    @property
    def best_index(self) -> int:
        return max((s.index for s in self.sessions), default=0)

    @property
    def last(self) -> Optional[Session]:
        return self.sessions[-1] if self.sessions else None

    @property
    def level(self):
        return level_for(self.best_index)

    def trend(self) -> str:
        if len(self.sessions) < 2:
            return "Not enough history yet - play one more session to see a trend."
        delta = self.sessions[-1].index - self.sessions[-2].index
        if delta > 25:
            return f"Up {delta} points since last session."
        if delta < -25:
            return f"Down {abs(delta)} points since last session. One session is noise; watch the next one."
        return "Holding steady since last session."

    def history_chart(self, width: int = 30) -> str:
        if not self.sessions:
            return "  (no sessions yet)"
        rows = []
        for s in self.sessions[-10:]:
            filled = int(round(s.index / 1000 * width))
            bar = "#" * filled + "." * (width - filled)
            rows.append(f"  {s.when}  [{bar}] {s.index:4d}  {s.level}")
        return "\n".join(rows)

    def to_dict(self) -> dict:
        return {"name": self.name, "sessions": [asdict(s) for s in self.sessions]}

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(
            name=data["name"],
            sessions=[Session(**s) for s in data.get("sessions", [])],
        )


class Store:
    def __init__(self, directory: str = DEFAULT_DIR):
        self.directory = directory
        self.path = os.path.join(directory, STORE_FILE)
        self.players: Dict[str, Player] = {}
        self.load()

    def load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            self.players = {k: Player.from_dict(v) for k, v in raw.items()}
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
            self.players = {}

    def save(self) -> None:
        try:
            os.makedirs(self.directory, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump({k: p.to_dict() for k, p in self.players.items()}, fh, indent=2)
        except OSError:
            pass  # a read-only home should never break a session

    def get(self, name: str) -> Player:
        key = name.strip().lower() or "guest"
        if key not in self.players:
            self.players[key] = Player(name=name.strip() or "guest")
        return self.players[key]

    def record(self, player: Player, report: Report) -> Session:
        session = Session.from_report(report)
        player.sessions.append(session)
        self.players[player.name.strip().lower()] = player
        self.save()
        return session

    def leaderboard(self, top: int = 10):
        ranked = sorted(self.players.values(), key=lambda p: p.best_index, reverse=True)
        return ranked[:top]
