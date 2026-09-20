"""The six Zen levels of MindZen.

A level is earned from the MindZen Index (0-1000), a blend of
intellect, clarity and calm. The names move from scattered to still.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ZenLevel:
    order: int
    name: str
    tagline: str
    low: int
    high: int
    description: str
    mantra: str
    next_step: str

    def contains(self, index: int) -> bool:
        return self.low <= index <= self.high

    @property
    def badge(self) -> str:
        return f"Zen {self.order} - {self.name}"


LEVELS: List[ZenLevel] = [
    ZenLevel(
        order=1,
        name="Dust",
        tagline="Scattered, but moving",
        low=0,
        high=249,
        description=(
            "Attention is blown around by whatever arrives first. Answers come "
            "either too fast or not at all, and pressure changes the result a lot."
        ),
        mantra="Before you solve it, read it twice.",
        next_step="Work on finishing a problem before judging it. Speed is not the goal yet.",
    ),
    ZenLevel(
        order=2,
        name="Pebble",
        tagline="Small weight, settling down",
        low=250,
        high=424,
        description=(
            "You can hold a problem still long enough to start it. Accuracy is "
            "real but fragile - a timer or a distraction still knocks it over."
        ),
        mantra="One thing, all the way through.",
        next_step="Practise restating each problem in your own words before answering.",
    ),
    ZenLevel(
        order=3,
        name="Ripple",
        tagline="Thinking spreads outward",
        low=425,
        high=574,
        description=(
            "Patterns start arriving on their own. You recover from a bad item "
            "instead of spiralling, though stress still costs you noticeable accuracy."
        ),
        mantra="A mistake is data, not a verdict.",
        next_step="Train the reset: after any wrong answer, take one slow breath before the next.",
    ),
    ZenLevel(
        order=4,
        name="Bamboo",
        tagline="Bends under load, does not break",
        low=575,
        high=724,
        description=(
            "Solid reasoning that mostly survives a countdown. You hesitate in the "
            "right places and commit in the right places."
        ),
        mantra="Flexible spine, fixed roots.",
        next_step="Push difficulty rather than speed - accuracy at hard items is your growth edge.",
    ),
    ZenLevel(
        order=5,
        name="Lotus",
        tagline="Clear thought in muddy water",
        low=725,
        high=874,
        description=(
            "Pressure barely moves your performance. You separate the signal from "
            "the noise quickly and your timing is consistent across item types."
        ),
        mantra="The mud is the condition, not the obstacle.",
        next_step="Practise under deliberate disadvantage: harder items, shorter clocks, no warm-up.",
    ),
    ZenLevel(
        order=6,
        name="Still Water",
        tagline="Nothing added, nothing disturbed",
        low=875,
        high=1000,
        description=(
            "Intellect, clarity and calm are all high and, more importantly, they "
            "hold together. Stress rounds look almost identical to calm rounds."
        ),
        mantra="A quiet mind reflects the problem exactly as it is.",
        next_step="Teach it. Explaining your method to someone else is the remaining gain.",
    ),
]


def level_for(index: int) -> ZenLevel:
    index = max(0, min(1000, int(index)))
    for level in LEVELS:
        if level.contains(index):
            return level
    return LEVELS[-1]


def progress_to_next(index: int):
    """Return (next_level, points_needed) or (None, 0) at the top level."""
    current = level_for(index)
    if current.order == len(LEVELS):
        return None, 0
    nxt = LEVELS[current.order]  # order is 1-based, so this is the next one
    return nxt, max(0, nxt.low - int(index))
