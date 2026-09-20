"""The six MindZen games.

Each game exposes .play(io, item, stressed) -> Attempt.
The app picks items, decides which rounds are pressure rounds and
collects the attempts; games stay dumb and reusable.
"""

import random
import re
from typing import List

from . import problems
from .scoring import Attempt

BASE_LIMITS = {  # seconds allowed in a calm round, by difficulty
    1: 35.0,
    2: 45.0,
    3: 60.0,
}
STRESS_FACTOR = 0.55  # pressure rounds cut the clock by 45%


def _normalise(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9 .\-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def check(given: str, item: dict) -> bool:
    given_n = _normalise(given)
    if not given_n:
        return False
    answers = [_normalise(a) for a in item["answers"]]
    if item.get("kind") == "keyword":
        return any(a and a in given_n for a in answers)
    if given_n in answers:
        return True
    # numeric tolerance: "36." / "36 rupees" / " 36"
    numbers = re.findall(r"-?\d+\.?\d*", given_n)
    if numbers:
        for a in answers:
            if a.replace(".", "", 1).lstrip("-").isdigit() and numbers[0].rstrip(".") == a:
                return True
    return False


def limit_for(difficulty: int, stressed: bool) -> float:
    base = BASE_LIMITS.get(difficulty, 45.0)
    return round(base * STRESS_FACTOR, 1) if stressed else base


class Game:
    name = "game"
    skill = "general"
    blurb = ""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def items(self) -> List[dict]:
        raise NotImplementedError

    def render(self, item: dict) -> str:
        prompt = item["prompt"]
        if item.get("options"):
            letters = "abcdefgh"
            lines = [f"     {letters[i]}) {opt}" for i, opt in enumerate(item["options"])]
            prompt += "\n" + "\n".join(lines)
        return prompt

    def play(self, io, item: dict, stressed: bool, show_header: bool = True) -> Attempt:
        limit = limit_for(item["difficulty"], stressed)
        setattr(io, "stressed", stressed)

        if show_header:
            io.say()
            io.say(io.c(f"  [{self.name}]  difficulty {item['difficulty']}/3", "magenta"))
            if stressed:
                io.say(io.c("  " + self.rng.choice(problems.DISTRACTORS), "red"))
        io.say()
        io.say("  " + self.render(item).replace("\n", "\n  "))
        io.say()

        given, elapsed, timed_out = io.ask("", limit, expected=item["answers"])
        correct = (not timed_out) and check(given, item)

        if correct:
            io.say(io.c("  correct.", "green"))
        elif timed_out:
            io.say(io.c("  no answer in time.", "red"))
        else:
            io.say(io.c(f"  not this time - answer: {item['answers'][0]}", "yellow"))
        io.say(io.c(f"  why: {item['explain']}", "dim"))

        return Attempt(
            game=self.name,
            skill=self.skill,
            difficulty=item["difficulty"],
            correct=correct,
            elapsed=elapsed,
            time_limit=limit,
            stressed=stressed,
            timed_out=timed_out,
            answer_given=given,
        )


class PatternGame(Game):
    name = "Sequence Sight"
    skill = "pattern"
    blurb = "Find the rule hiding inside a run of numbers or letters."

    def items(self):
        return list(problems.SEQUENCES)

    def render(self, item):
        return f"What comes next?\n\n   {item['prompt']}"


class LogicGame(Game):
    name = "Clean Reasoning"
    skill = "logic"
    blurb = "Traps for fast intuition. Slow down or lose."

    def items(self):
        return list(problems.LOGIC)


class FocusGame(Game):
    name = "Interference"
    skill = "focus"
    blurb = "The obvious reading is wrong. Hold the real instruction."

    def items(self):
        return list(problems.FOCUS)


class NumericGame(Game):
    name = "Number Rush"
    skill = "numeric"
    blurb = "Mental arithmetic against a clock."

    def items(self):
        return list(problems.NUMERIC)


class LateralGame(Game):
    name = "Sideways"
    skill = "lateral"
    blurb = "Reframe the question instead of attacking it."

    def items(self):
        return list(problems.LATERAL)


class MemoryGame(Game):
    """Shown briefly, then hidden. Recall exactly, in order."""

    name = "Held in Mind"
    skill = "memory"
    blurb = "Working memory: see it, lose it, rebuild it."

    def items(self):
        out = []
        for raw in problems.MEMORY:
            out.append(
                {
                    "payload": raw["payload"],
                    "prompt": "Recall the sequence in order (spaces between items).",
                    "answers": [raw["payload"].lower()],
                    "difficulty": raw["difficulty"],
                    "explain": raw["explain"],
                }
            )
        return out

    def play(self, io, item, stressed):
        setattr(io, "stressed", stressed)
        show_time = 2.5 if stressed else 4.0
        io.say()
        io.say(io.c(f"  [{self.name}]  difficulty {item['difficulty']}/3", "magenta"))
        if stressed:
            io.say(io.c("  " + self.rng.choice(problems.DISTRACTORS), "red"))
        io.say(io.c(f"  memorise this - it disappears in {show_time:.0f}s", "dim"))
        io.flash("\n      " + io.c(item["payload"], "bold") + "\n", show_time)
        return super().play(io, item, stressed, show_header=False)


ALL_GAMES = [PatternGame, LogicGame, MemoryGame, FocusGame, NumericGame, LateralGame]


def build_games(rng: random.Random | None = None) -> List[Game]:
    return [cls(rng) for cls in ALL_GAMES]
