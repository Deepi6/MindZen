"""MindZen - a brainstorming, critical-thinking and composure platform.

mind = intelligence,  zen = clarity and calm.
"""

__version__ = "1.0.0"

from .scoring import Attempt, evaluate, Report  # noqa: F401
from .zen import LEVELS, ZenLevel, level_for  # noqa: F401
