"""Terminal input/output, including input with a hard time limit.

ConsoleIO is the real thing. BotIO simulates a player so the whole
platform can be run head-less (`--demo`, tests, tuning the scoring).
"""

import os
import random
import sys
import time

WIDTH = 66

_ANSI = {
    "reset": "\033[0m",
    "dim": "\033[2m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "magenta": "\033[35m",
}


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


class ConsoleIO:
    def __init__(self, color: bool | None = None, slow: bool = True):
        self.color = _supports_color() if color is None else color
        self.slow = slow

    # ---------- output ----------
    def c(self, text: str, style: str) -> str:
        if not self.color:
            return text
        return f"{_ANSI.get(style, '')}{text}{_ANSI['reset']}"

    def say(self, text: str = "") -> None:
        print(text)

    def rule(self, char: str = "-") -> None:
        self.say(self.c(char * WIDTH, "dim"))

    def header(self, title: str) -> None:
        self.say()
        self.rule("=")
        self.say(self.c(f"  {title}", "bold"))
        self.rule("=")

    def banner(self) -> None:
        art = r"""
   __  __ _         _ ____
  |  \/  (_)_ _  __| |_  /___ _ _
  | |\/| | | ' \/ _` |/ // -_) ' \
  |_|  |_|_|_||_\__,_/___\___|_||_|
"""
        self.say(self.c(art, "cyan"))
        self.say(self.c("  mind for intelligence  .  zen for clarity and calm", "dim"))
        self.rule("=")

    def wait(self, seconds: float) -> None:
        if self.slow:
            time.sleep(seconds)

    def pause(self, message: str = "Press Enter to continue...") -> None:
        try:
            input(self.c(f"\n  {message} ", "dim"))
        except EOFError:
            pass

    def flash(self, text: str, seconds: float) -> None:
        """Show something briefly, then scroll it out of sight."""
        print(text)
        self.wait(seconds)
        print("\n" * 40)

    # ---------- input ----------
    def ask_plain(self, prompt: str, default: str = "") -> str:
        try:
            value = input(self.c(prompt, "cyan"))
        except EOFError:
            return default
        return value.strip() or default

    def ask(self, prompt: str, limit: float, expected=None):
        """Ask a question with a time limit.

        Returns (text, elapsed_seconds, timed_out).
        `expected` is ignored here; BotIO uses it.
        """
        print(prompt)
        print(self.c(f"  clock: {limit:.0f}s", "yellow"))
        sys.stdout.write(self.c("  > ", "cyan"))
        sys.stdout.flush()

        start = time.monotonic()
        text = self._read_with_timeout(limit)
        elapsed = time.monotonic() - start

        if text is None:
            print(self.c("\n  [time]  the clock ran out.", "red"))
            return "", limit, True
        return text.strip(), min(elapsed, limit), False

    def _read_with_timeout(self, limit: float):
        """POSIX select-based read; falls back to a blocking read elsewhere."""
        try:
            import select

            if not sys.stdin.isatty():
                raise OSError("not a tty")
            ready, _, _ = select.select([sys.stdin], [], [], limit)
            if ready:
                return sys.stdin.readline()
            return None
        except Exception:
            # Windows or a non-tty stdin: read normally and let the caller
            # rely on measured elapsed time rather than a hard cut-off.
            try:
                return sys.stdin.readline()
            except (EOFError, KeyboardInterrupt):
                return None


class BotIO(ConsoleIO):
    """A simulated player. Useful for demos, tests and scoring calibration."""

    def __init__(self, skill: float = 0.7, composure: float = 0.7, quiet: bool = False, seed=None):
        super().__init__(color=False, slow=False)
        self.skill = skill            # 0..1 chance of knowing the answer
        self.composure = composure    # 0..1 resistance to the pressure penalty
        self.quiet = quiet
        self.rng = random.Random(seed)
        self.stressed = False

    def say(self, text: str = "") -> None:
        if not self.quiet:
            print(text)

    def flash(self, text: str, seconds: float) -> None:
        self.say(text)

    def pause(self, message: str = "") -> None:
        return

    def wait(self, seconds: float) -> None:
        return

    def ask_plain(self, prompt: str, default: str = "") -> str:
        self.say(prompt + default)
        return default

    def ask(self, prompt: str, limit: float, expected=None):
        self.say(prompt)
        chance = self.skill
        if self.stressed:
            chance *= 0.55 + 0.45 * self.composure
        correct = self.rng.random() < chance
        pace = self.rng.uniform(0.35, 0.85)
        if self.stressed:
            pace = min(1.0, pace + (1 - self.composure) * 0.4)
        elapsed = round(limit * pace, 2)

        if correct and expected:
            answer = str(expected[0] if isinstance(expected, (list, tuple)) else expected)
        else:
            answer = self.rng.choice(["0", "nope", "42", ""])
            if self.rng.random() < (1 - self.composure) * 0.5:
                elapsed = round(limit * self.rng.uniform(0.05, 0.25), 2)  # snap guess
        self.say(f"  > {answer}   ({elapsed}s)")
        return answer, elapsed, False
