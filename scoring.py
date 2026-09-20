"""Scoring engine.

Three dimensions are measured, never a single number:

  Intellect - difficulty-weighted accuracy. What you can solve.
  Clarity   - timing margin, consistency and absence of impulsive errors.
              How cleanly you solve it.
  Calm      - how much of your calm-round performance survives the
              pressure rounds. What is left of you under load.

MindZen Index = 10 * (0.40*intellect + 0.30*clarity + 0.30*calm)  ->  0..1000
"""

from dataclasses import dataclass, asdict, field
from statistics import mean, pstdev
from typing import Dict, List

WEIGHTS = {"intellect": 0.40, "clarity": 0.30, "calm": 0.30}


@dataclass
class Attempt:
    """One answered (or missed) item."""

    game: str
    skill: str          # pattern | logic | memory | focus | numeric | lateral
    difficulty: int     # 1 easy, 2 medium, 3 hard
    correct: bool
    elapsed: float      # seconds actually taken
    time_limit: float   # seconds allowed
    stressed: bool      # was this a pressure round?
    timed_out: bool = False
    answer_given: str = ""

    @property
    def ratio(self) -> float:
        if self.time_limit <= 0:
            return 1.0
        return min(1.5, self.elapsed / self.time_limit)

    def to_dict(self) -> dict:
        return asdict(self)


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass
class Report:
    intellect: float
    clarity: float
    calm: float
    index: int
    accuracy: float
    accuracy_calm: float
    accuracy_stress: float
    retention: float
    avg_ratio: float
    impulsive_rate: float
    timeout_rate: float
    consistency: float
    skills: Dict[str, float] = field(default_factory=dict)
    attempts: int = 0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["index"] = int(self.index)
        return data


def _intellect(attempts: List[Attempt]) -> float:
    total = sum(a.difficulty for a in attempts)
    if not total:
        return 0.0
    earned = sum(a.difficulty for a in attempts if a.correct)
    # A small bonus for solving hard items, a small floor-raise for finishing at all.
    hard = [a for a in attempts if a.difficulty >= 3]
    bonus = 0.0
    if hard:
        bonus = 6.0 * (sum(1 for a in hard if a.correct) / len(hard))
    return _clip(100.0 * earned / total + bonus, 0, 100)


def _clarity(attempts: List[Attempt]) -> float:
    if not attempts:
        return 0.0
    # Speed margin: clock left unused on the items you actually got right.
    # Wrong and timed-out items contribute nothing, so speed without
    # correctness cannot buy clarity.
    margin = mean(_clip(1.0 - a.ratio) if a.correct else 0.0 for a in attempts)

    # Consistency: stable pacing across items (low coefficient of variation).
    ratios = [a.ratio for a in attempts]
    m = mean(ratios)
    cv = (pstdev(ratios) / m) if m > 0 else 1.0
    consistency = _clip(1.0 - cv)

    # Impulsivity: wrong answers fired off in under 30% of the allowed time.
    impulsive = sum(1 for a in attempts if not a.correct and not a.timed_out and a.ratio < 0.30)
    impulsive_rate = impulsive / len(attempts)

    # Freezing: items that ran out the clock entirely.
    timeout_rate = sum(1 for a in attempts if a.timed_out) / len(attempts)

    score = (
        0.45 * margin
        + 0.25 * consistency
        + 0.20 * (1.0 - impulsive_rate)
        + 0.10 * (1.0 - timeout_rate)
    )
    return _clip(score) * 100.0


def _calm(attempts: List[Attempt]) -> float:
    calm_items = [a for a in attempts if not a.stressed]
    hot_items = [a for a in attempts if a.stressed]
    if not hot_items:
        return 50.0  # no pressure was applied; report a neutral value

    acc_hot = sum(1 for a in hot_items if a.correct) / len(hot_items)
    if calm_items:
        acc_calm = sum(1 for a in calm_items if a.correct) / len(calm_items)
    else:
        acc_calm = acc_hot

    # Retention: what fraction of baseline accuracy survived the pressure.
    if acc_calm > 0:
        retention = _clip(acc_hot / acc_calm, 0, 1.15)
    else:
        retention = acc_hot

    # Retention only means something if the baseline was worth keeping:
    # failing equally in both phases is not composure. Shrink it towards
    # the baseline, then blend with raw performance under pressure.
    retention_eff = _clip(retention) * (0.5 + 0.5 * acc_calm)
    composure = 0.55 * retention_eff + 0.45 * acc_hot

    # Pacing stability: did your time usage blow up under pressure?
    r_hot = mean(a.ratio for a in hot_items)
    r_calm = mean(a.ratio for a in calm_items) if calm_items else r_hot
    stability = _clip(1.0 - max(0.0, r_hot - r_calm))

    # Panic: timeouts and snap-guesses concentrated in the pressure rounds.
    panic = sum(
        1 for a in hot_items if a.timed_out or (not a.correct and a.ratio < 0.30)
    ) / len(hot_items)

    # Steady pacing is only credited to the extent that something was
    # actually solved under pressure - calm without output is not calm.
    grounding = 0.35 + 0.65 * acc_hot
    score = 0.60 * composure + (0.25 * stability + 0.15 * (1.0 - panic)) * grounding
    return _clip(score) * 100.0


def _skill_breakdown(attempts: List[Attempt]) -> Dict[str, float]:
    buckets: Dict[str, List[Attempt]] = {}
    for a in attempts:
        buckets.setdefault(a.skill, []).append(a)
    out = {}
    for skill, items in buckets.items():
        total = sum(i.difficulty for i in items)
        earned = sum(i.difficulty for i in items if i.correct)
        out[skill] = round(100.0 * earned / total, 1) if total else 0.0
    return out


def evaluate(attempts: List[Attempt]) -> Report:
    if not attempts:
        return Report(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, {}, 0)

    intellect = _intellect(attempts)
    clarity = _clarity(attempts)
    calm = _calm(attempts)
    index = round(
        10 * (WEIGHTS["intellect"] * intellect + WEIGHTS["clarity"] * clarity + WEIGHTS["calm"] * calm)
    )

    calm_items = [a for a in attempts if not a.stressed]
    hot_items = [a for a in attempts if a.stressed]
    acc = sum(1 for a in attempts if a.correct) / len(attempts)
    acc_calm = (sum(1 for a in calm_items if a.correct) / len(calm_items)) if calm_items else 0.0
    acc_hot = (sum(1 for a in hot_items if a.correct) / len(hot_items)) if hot_items else 0.0
    retention = (acc_hot / acc_calm) if acc_calm > 0 else acc_hot

    ratios = [a.ratio for a in attempts]
    m = mean(ratios)
    cv = (pstdev(ratios) / m) if m > 0 else 1.0

    return Report(
        intellect=round(intellect, 1),
        clarity=round(clarity, 1),
        calm=round(calm, 1),
        index=int(_clip(index, 0, 1000)),
        accuracy=round(acc * 100, 1),
        accuracy_calm=round(acc_calm * 100, 1),
        accuracy_stress=round(acc_hot * 100, 1),
        retention=round(min(retention, 1.5), 2),
        avg_ratio=round(m, 2),
        impulsive_rate=round(
            sum(1 for a in attempts if not a.correct and not a.timed_out and a.ratio < 0.30)
            / len(attempts),
            2,
        ),
        timeout_rate=round(sum(1 for a in attempts if a.timed_out) / len(attempts), 2),
        consistency=round(_clip(1 - cv) * 100, 1),
        skills=_skill_breakdown(attempts),
        attempts=len(attempts),
    )
