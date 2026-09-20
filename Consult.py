"""The consultation half of MindZen.

Scores alone help nobody. This module reads a Report and produces a
plain-language debrief: what the numbers mean, what is probably going
wrong, and a short set of practices that target the weakest dimension.

This is a self-reflection and training tool. It is not a psychological
assessment, a diagnosis, or a substitute for professional care.
"""

from dataclasses import dataclass
from typing import List

from .scoring import Report
from .zen import level_for, progress_to_next

DISCLAIMER = (
    "MindZen is a training and self-reflection tool, not a clinical test. "
    "Its scores describe how you played today, not who you are. If stress, "
    "focus or low mood is affecting your daily life, talking to a doctor or "
    "a qualified mental health professional is worth far more than any score."
)

BAND_LOW, BAND_MID = 55.0, 75.0


def band(value: float) -> str:
    if value < BAND_LOW:
        return "needs work"
    if value < BAND_MID:
        return "developing"
    return "strong"


@dataclass
class Prescription:
    title: str
    why: str
    practices: List[str]
    drill: str


INTELLECT_LOW = Prescription(
    title="Build the toolkit before the speed",
    why=(
        "You lost most points on difficulty rather than on the clock. That is a "
        "knowledge-and-method gap, which is the easiest kind to close."
    ),
    practices=[
        "Keep a 'missed item' notebook. Write the problem, your answer, and the rule you missed.",
        "Re-solve yesterday's misses before starting anything new.",
        "Say the method out loud before computing - naming the approach beats guessing at it.",
        "Work one difficulty level below your ceiling until accuracy is above 80%, then step up.",
    ],
    drill="10 minutes daily: 5 sequence items and 3 logic items, no timer at all.",
)

CLARITY_LOW = Prescription(
    title="Stop answering before you have finished reading",
    why=(
        "Your wrong answers arrived fast and your pacing was uneven. That is an "
        "impulse-control pattern, not a reasoning failure - you often knew it."
    ),
    practices=[
        "Two-pass rule: read the question once for content, once for the actual instruction.",
        "Before typing, finish this sentence in your head: 'The question is asking me to...'",
        "Insert a deliberate 3-second delay before every answer for one full session.",
        "After answering, spend 2 seconds checking the answer against the question, not your gut.",
    ],
    drill="Play Interference and Clean Reasoning only, with a forced pause before each answer.",
)

CALM_LOW = Prescription(
    title="Train the recovery, not the pressure tolerance",
    why=(
        "Your accuracy dropped sharply once the clock shortened. The skill was "
        "there in calm rounds, so what you are training is the reset, not the reasoning."
    ),
    practices=[
        "Box breathing before a pressure round: in 4, hold 4, out 4, hold 4, twice through.",
        "Physiological sigh when you feel the spike: two short inhales through the nose, one long exhale.",
        "Name the state instead of fighting it: 'this is arousal, it is not danger'.",
        "One-item horizon: after a miss, the only task is the next item. Do not total the score mid-game.",
        "Unclench on purpose - jaw, shoulders, hands. The body leads the mind back down.",
    ],
    drill="Alternate one calm round and one pressure round, with 60 seconds of breathing between them.",
)

BALANCED = Prescription(
    title="Hold the line and raise the load",
    why="No dimension is dragging. Growth now comes from harder conditions, not more repetitions.",
    practices=[
        "Raise difficulty before raising speed.",
        "Play cold - no warm-up round - so the first item is the hard one.",
        "Explain each solution to someone else; gaps show up instantly when spoken.",
        "Keep one session a week fully untimed to protect the quality of your thinking.",
    ],
    drill="A full session at difficulty 3 with pressure rounds throughout, twice a week.",
)

SKILL_NOTES = {
    "pattern": "Pattern work: look at the gaps between terms before the terms themselves.",
    "logic": "Logic work: the first answer that feels obvious in these items is usually the trap.",
    "memory": "Memory work: chunk into groups of 2-3 and rehearse out loud while the display is up.",
    "focus": "Focus work: underline the actual instruction word ('letters', 'words', 'capitals') first.",
    "numeric": "Numeric work: estimate the size of the answer before computing it exactly.",
    "lateral": "Lateral work: ask what assumption you added that the question never stated.",
}


def prescriptions(report: Report) -> List[Prescription]:
    ranked = sorted(
        [("intellect", report.intellect), ("clarity", report.clarity), ("calm", report.calm)],
        key=lambda pair: pair[1],
    )
    weakest, value = ranked[0]
    out: List[Prescription] = []
    if value >= BAND_MID:
        out.append(BALANCED)
    else:
        out.append({"intellect": INTELLECT_LOW, "clarity": CLARITY_LOW, "calm": CALM_LOW}[weakest])
        second, second_value = ranked[1]
        if second_value < BAND_LOW:
            out.append({"intellect": INTELLECT_LOW, "clarity": CLARITY_LOW, "calm": CALM_LOW}[second])
    return out


def observations(report: Report) -> List[str]:
    notes = []
    if report.timeout_rate >= 0.2:
        notes.append(
            f"You ran out the clock on {int(report.timeout_rate * 100)}% of items - "
            "that is freezing, not slowness. A partial answer beats an empty one."
        )
    if report.impulsive_rate >= 0.2:
        notes.append(
            f"{int(report.impulsive_rate * 100)}% of items were wrong answers given in under "
            "a third of the time allowed. Speed is costing you points you had already earned."
        )
    if report.consistency < 45:
        notes.append(
            "Your pacing swings hard between items - some rushed, some laboured. "
            "Even pacing usually lifts accuracy on its own."
        )
    if report.accuracy_calm - report.accuracy_stress >= 25:
        notes.append(
            f"Calm accuracy {report.accuracy_calm}% vs pressure accuracy {report.accuracy_stress}%. "
            "The knowledge is there; the pressure round is where it leaks."
        )
    elif report.accuracy_stress >= report.accuracy_calm and report.attempts >= 6:
        notes.append(
            "You performed at least as well under pressure as without it. "
            "Deadlines appear to focus you rather than rattle you."
        )
    weak_skills = [s for s, v in report.skills.items() if v < 50]
    for skill in weak_skills[:2]:
        if skill in SKILL_NOTES:
            notes.append(SKILL_NOTES[skill])
    if not notes:
        notes.append("A clean session - no freezing, no snap-guessing, steady pacing throughout.")
    return notes


def debrief(report: Report) -> str:
    """Full text consultation for one session."""
    level = level_for(report.index)
    nxt, gap = progress_to_next(report.index)
    lines = []
    add = lines.append

    add("")
    add(f"  MindZen Index : {report.index} / 1000")
    add(f"  Zen level     : {level.badge}  -  {level.tagline}")
    add("")
    add(f"  Intellect  {report.intellect:5.1f}  {_bar(report.intellect)}  {band(report.intellect)}")
    add(f"  Clarity    {report.clarity:5.1f}  {_bar(report.clarity)}  {band(report.clarity)}")
    add(f"  Calm       {report.calm:5.1f}  {_bar(report.calm)}  {band(report.calm)}")
    add("")
    add(f"  Accuracy: {report.accuracy}%   (calm {report.accuracy_calm}% / pressure {report.accuracy_stress}%)")
    if report.skills:
        parts = "   ".join(f"{k}:{v:.0f}" for k, v in sorted(report.skills.items()))
        add(f"  By skill: {parts}")
    add("")
    add("  WHAT THIS LEVEL MEANS")
    add(f"  {level.description}")
    add(f"  Mantra: \"{level.mantra}\"")
    if nxt:
        add(f"  Next level: {nxt.name} - {gap} index points away.")
    add("")
    add("  WHAT I NOTICED")
    for note in observations(report):
        add(f"  - {note}")
    add("")
    add("  YOUR PLAN")
    for p in prescriptions(report):
        add(f"  {p.title}")
        add(f"  {p.why}")
        for practice in p.practices:
            add(f"    * {practice}")
        add(f"    Drill: {p.drill}")
        add("")
    add("  NOTE")
    add(f"  {DISCLAIMER}")
    add("")
    return "\n".join(lines)


def _bar(value: float, width: int = 20) -> str:
    filled = int(round(_c(value) / 100 * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def _c(value: float) -> float:
    return max(0.0, min(100.0, value))
