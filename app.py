"""MindZen application flow.

A session has three phases:

  1. Stillness   - calibration. Generous clocks, no noise. This is your baseline.
  2. Storm       - the same kinds of problems with the clock cut by 45%,
                   plus distractions and score pressure.
  3. Debrief     - three scores, a Zen level, and a consultation.
"""

import argparse
import random
import sys
from typing import List

from . import consult
from .games import build_games
from .profile import Store
from .scoring import Attempt, evaluate
from .ui import BotIO, ConsoleIO
from .zen import LEVELS, level_for

CALM_ITEMS = 6
STORM_ITEMS = 6


def pick_items(games, count: int, rng: random.Random, used: set) -> List[tuple]:
    """Pick (game, item) pairs spread across games, avoiding repeats."""
    pool = []
    for game in games:
        for item in game.items():
            key = (game.name, item.get("prompt", "") + item.get("payload", ""))
            if key not in used:
                pool.append((game, item, key))
    rng.shuffle(pool)

    chosen, per_game = [], {}
    # First pass: at most one item per game, so a session always touches
    # every kind of thinking. Later passes fill any remaining slots.
    cap = 1
    while len(chosen) < count and cap <= count:
        for game, item, key in pool:
            if len(chosen) >= count:
                break
            if key in used or per_game.get(game.name, 0) >= cap:
                continue
            per_game[game.name] = per_game.get(game.name, 0) + 1
            used.add(key)
            chosen.append((game, item))
        cap += 1
    rng.shuffle(chosen)
    return chosen


def run_phase(io, games, count, stressed, rng, used) -> List[Attempt]:
    attempts = []
    for number, (game, item) in enumerate(pick_items(games, count, rng, used), start=1):
        io.say()
        io.rule()
        label = "STORM" if stressed else "STILLNESS"
        io.say(io.c(f"  {label}  item {number}/{count}", "bold"))
        attempts.append(game.play(io, item, stressed))
    return attempts


def breathing(io, cycles: int = 3) -> None:
    """Box breathing between the phases. Also available from the menu."""
    io.header("The Calm Room")
    io.say("  Box breathing. In for 4, hold 4, out 4, hold 4.")
    io.say(io.c("  Nothing is being scored here.", "dim"))
    for cycle in range(1, cycles + 1):
        io.say(f"\n  cycle {cycle}/{cycles}")
        for phase in ("breathe in ....", "hold ...........", "breathe out ...", "hold ..........."):
            io.say(io.c(f"    {phase}", "cyan"))
            io.wait(4)
    io.say("\n  Shoulders down. Jaw loose. Ready.")


def play_session(io, store: Store, player_name: str, rng: random.Random) -> None:
    games = build_games(rng)
    used: set = set()

    io.header("PHASE 1 - STILLNESS")
    io.say("  Full clocks, no interruptions. This is your baseline.")
    io.say(io.c("  Answer honestly, not quickly.", "dim"))
    io.pause()
    calm_attempts = run_phase(io, games, CALM_ITEMS, False, rng, used)

    breathing(io, cycles=2)
    io.pause("Press Enter when you are ready for the storm...")

    io.header("PHASE 2 - STORM")
    io.say("  Same thinking. 45% less time. Some noise on the side.")
    io.say(io.c("  What you keep here is what you actually own.", "dim"))
    io.pause()
    storm_attempts = run_phase(io, games, STORM_ITEMS, True, rng, used)

    report = evaluate(calm_attempts + storm_attempts)
    io.header("PHASE 3 - DEBRIEF")
    io.say(consult.debrief(report))

    player = store.get(player_name)
    store.record(player, report)
    io.say(f"  {player.trend()}")
    io.say(f"  Best index so far: {player.best_index}  ({player.level.badge})")
    io.say()


def show_levels(io) -> None:
    io.header("THE SIX ZEN LEVELS")
    for level in LEVELS:
        io.say()
        io.say(io.c(f"  {level.badge}   ({level.low}-{level.high})", "bold"))
        io.say(f"  {level.tagline}")
        io.say(io.c(f"  {level.description}", "dim"))
        io.say(io.c(f"  mantra: \"{level.mantra}\"", "cyan"))
    io.say()


def show_progress(io, store: Store, name: str) -> None:
    player = store.get(name)
    io.header(f"PROGRESS - {player.name}")
    if not player.sessions:
        io.say("  No sessions recorded yet.")
        return
    io.say(player.history_chart())
    io.say()
    io.say(f"  Best: {player.best_index}   Level: {player.level.badge}")
    io.say(f"  {player.trend()}")
    io.say()


def show_leaderboard(io, store: Store) -> None:
    io.header("LEADERBOARD")
    board = store.leaderboard()
    if not board:
        io.say("  Nobody has played yet.")
        return
    for rank, player in enumerate(board, start=1):
        io.say(f"  {rank:2d}. {player.name:<16} {player.best_index:4d}   {player.level.badge}")
    io.say()
    io.say(io.c("  Rank is a side effect here, not the point.", "dim"))


def menu(io, store: Store, name: str, rng: random.Random) -> None:
    while True:
        io.header("MAIN MENU")
        io.say("  1) Play a full session   (stillness -> storm -> debrief)")
        io.say("  2) The Calm Room         (breathing, nothing scored)")
        io.say("  3) The six Zen levels")
        io.say("  4) My progress")
        io.say("  5) Leaderboard")
        io.say("  6) Quit")
        choice = io.ask_plain("\n  choose > ", default="6")

        if choice == "1":
            play_session(io, store, name, rng)
        elif choice == "2":
            breathing(io)
        elif choice == "3":
            show_levels(io)
        elif choice == "4":
            show_progress(io, store, name)
        elif choice == "5":
            show_leaderboard(io, store)
        elif choice in ("6", "q", "quit", "exit"):
            io.say("\n  Take the calm with you. See you next session.\n")
            return
        else:
            io.say(io.c("  Not an option.", "yellow"))


def demo(seed: int = 7, skill: float = 0.75, composure: float = 0.45, quiet: bool = False) -> int:
    """Run a full simulated session. Returns the MindZen Index."""
    rng = random.Random(seed)
    io = BotIO(skill=skill, composure=composure, quiet=quiet, seed=seed)
    store = Store(directory="./.mindzen-demo")
    games = build_games(rng)
    used: set = set()

    calm_attempts = run_phase(io, games, CALM_ITEMS, False, rng, used)
    storm_attempts = run_phase(io, games, STORM_ITEMS, True, rng, used)
    report = evaluate(calm_attempts + storm_attempts)

    print(consult.debrief(report))
    store.record(store.get("demo-bot"), report)
    return report.index


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="mindzen", description="MindZen - brainstorm, stay calm, get clear.")
    parser.add_argument("--name", help="player name")
    parser.add_argument("--demo", action="store_true", help="run a simulated session and exit")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    parser.add_argument("--no-color", action="store_true", help="plain output")
    parser.add_argument("--fast", action="store_true", help="skip the paced pauses (testing)")
    parser.add_argument("--levels", action="store_true", help="print the six Zen levels and exit")
    args = parser.parse_args(argv)

    if args.demo:
        demo(seed=args.seed if args.seed is not None else 7, quiet=True)
        return 0

    io = ConsoleIO(color=False if args.no_color else None, slow=not args.fast)
    if args.levels:
        show_levels(io)
        return 0

    rng = random.Random(args.seed)
    store = Store()

    io.banner()
    io.say()
    io.say("  Two things are measured here, not one.")
    io.say("  What you can solve, and what is left of you when it gets hard.")
    io.say()
    io.say(io.c("  " + consult.DISCLAIMER, "dim"))

    name = args.name or io.ask_plain("\n  Your name > ", default="guest")
    player = store.get(name)
    io.say(f"\n  Welcome, {player.name}. Current level: {player.level.badge}")

    try:
        menu(io, store, name, rng)
    except KeyboardInterrupt:
        io.say("\n\n  Stopped. Nothing wrong with walking away from a timer.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
