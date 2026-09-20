# MindZen

mind for intelligence, zen for clarity and calm.

A terminal platform that does two things at once: it gives you brainstorming
games and critical-thinking problems, and it measures what is left of your
thinking when the pressure goes up. Then it sits you down and talks you
through the result.

Pure Python 3.10+, standard library only. No installation, no dependencies.

bash
cd mindzen
python -m mindzen              # play
python -m mindzen --demo       # simulated session + full debrief, no typing
python -m mindzen --levels     # the six Zen levels
python -m unittest discover -s tests




## The idea

Most quiz apps score one thing: did you get it right. That misses the part
people actually struggle with. Someone can solve a problem perfectly on a
quiet afternoon and fall apart on the same problem with a clock on it and
someone watching. MindZen measures both, separately, and treats the gap
between them as the real finding.

A session runs in three phases:

| Phase | What happens |
|---|---|
| 1. Stillness | Six items, generous clocks, no noise. This is your baseline. |
| 2. Storm| Six more items, the clock cut by 45%, plus distraction lines and score pressure. |
| 3. Debrief | Three scores, a Zen level, and a consultation written for your specific profile. |

Between the phases there is a Calm Room: guided box breathing where
nothing at all is scored.

## The six games

| Game | Trains | What it is |
|---|---|---|
| Sequence Sight | pattern | Find the rule hiding in a run of numbers or letters |
| Clean Reasoning | logic | Bat-and-ball, Wason selection, syllogism traps |
| Held in Mind | memory | Digit and word spans shown briefly, then hidden |
| Interference | focus | The obvious reading is wrong; hold the real instruction |
| Number Rush | numeric | Mental arithmetic against a clock |
| Sideways | lateral | Riddles that need a reframe, not an attack |

Every session touches all six before repeating any of them.

## The three scores

Nothing here collapses into a single "IQ" number, because a single number
would hide the interesting part.

- Intellect — difficulty-weighted accuracy. *What you can solve.*
- Clarity — clock margin on correct answers, consistency of pacing, and
  the absence of snap-guessing and freezing. *How cleanly you solve it.*
- Calm — how much of your baseline accuracy survives the storm phase,
  plus pacing stability and panic markers. *What is left of you under load.*

```
MindZen Index = 10 × (0.40·Intellect + 0.30·Clarity + 0.30·Calm)   →   0–1000
```

Two safeguards are built into the maths, both covered by tests:

- Speed without correctness cannot buy Clarity. Wrong and timed-out items
  contribute zero clock margin.
- Failing equally in both phases is *not* composure. Retention is shrunk
  toward your baseline accuracy and blended with raw pressure performance,
  so uniform failure scores low on Calm rather than high.

## The six Zen levels

| # | Level | Index | Meaning |
|---|---|---|---|
| 1 | Dust | 0–249 | Scattered. Answers come too fast or not at all. |
| 2 | Pebble | 250–424 | Settling. Accuracy is real but fragile. |
| 3 | Ripple| 425–574 | Patterns arrive; you recover from bad items. |
| 4 | Bamboo | 575–724 | Bends under load, does not break. |
| 5 | Lotus| 725–874 | Clear thought in muddy water. |
| 6 | Still Water | 875–1000 | Storm rounds look like calm rounds. |

Each level carries a description, a mantra and a concrete next step.

## The consultation

`consult.py` is the half of the project that makes it more than a quiz. It
reads the score profile and produces:

- What I noticed — plain-language observations drawn from the actual
  telemetry: freeze rate, snap-guess rate, pacing swings, the calm-vs-storm
  accuracy gap, and which specific skills fell below 50.
- Your plan — a targeted prescription for the *weakest* dimension, not a
  generic list. Low Intellect gets method and notebook work. Low Clarity gets
  impulse control (two-pass reading, forced delay). Low Calm gets recovery
  training (box breathing, physiological sigh, one-item horizon). A balanced
  profile gets harder conditions instead of more repetitions.

Every report ends with a clear note that MindZen is a training and
self-reflection tool, not a clinical test or a diagnosis, and that persistent
difficulty with stress, focus or mood is worth a conversation with a
qualified professional. That line is deliberate and should stay in.

## Layout

```
mindzen/
├── mindzen/
│   ├── __main__.py     entry point
│   ├── app.py          session flow, menus, calm room, demo mode
│   ├── games.py        the six games, answer checking, stress clocks
│   ├── problems.py     the content bank
│   ├── scoring.py      Attempt → Report (intellect / clarity / calm / index)
│   ├── consult.py      observations, prescriptions, the written debrief
│   ├── profile.py      players, session history, JSON store, leaderboard
│   ├── zen.py          the six levels
│   └── ui.py           timed console input + a simulated player (BotIO)
├── tests/test_mindzen.py
└── README.md
```

Profiles are saved to `~/.mindzen/profiles.json`, or wherever `MINDZEN_HOME`
points.

## Extending it

- New problems: append a dict to the right list in `problems.py`. The test
  suite checks every stated answer passes its own checker.
- New game: subclass `Game`, set `name`/`skill`, return items from
  `items()`, add it to `ALL_GAMES`.
- Retune the model: the weights live at the top of `scoring.py` and in the
  three `_intellect` / `_clarity` / `_calm` functions. Run
  `python -m mindzen --demo` with different bot skill and composure values to
  see how the level distribution shifts before you commit to a change.
- Headless play: `BotIO(skill=…, composure=…)` simulates a player, which is
  how the scoring curve was calibrated and how the flow is tested.
