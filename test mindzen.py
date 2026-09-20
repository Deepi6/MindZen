"""Tests for MindZen. Run with:  python -m unittest discover -s tests"""

import unittest

from mindzen.games import check, limit_for, build_games
from mindzen.scoring import Attempt, evaluate
from mindzen.zen import LEVELS, level_for, progress_to_next
from mindzen.consult import band, debrief, prescriptions, CALM_LOW, INTELLECT_LOW
from mindzen.profile import Player, Session, Store


def attempt(correct=True, stressed=False, difficulty=2, ratio=0.5, timed_out=False):
    limit = 40.0
    return Attempt(
        game="t", skill="logic", difficulty=difficulty, correct=correct,
        elapsed=limit * ratio, time_limit=limit, stressed=stressed, timed_out=timed_out,
    )


class ZenLevelTests(unittest.TestCase):
    def test_six_levels_cover_the_whole_range_without_gaps(self):
        self.assertEqual(len(LEVELS), 6)
        self.assertEqual(LEVELS[0].low, 0)
        self.assertEqual(LEVELS[-1].high, 1000)
        for earlier, later in zip(LEVELS, LEVELS[1:]):
            self.assertEqual(later.low, earlier.high + 1)

    def test_level_lookup_and_clamping(self):
        self.assertEqual(level_for(0).name, "Dust")
        self.assertEqual(level_for(1000).name, "Still Water")
        self.assertEqual(level_for(-500).name, "Dust")
        self.assertEqual(level_for(99999).name, "Still Water")

    def test_progress_to_next(self):
        nxt, gap = progress_to_next(400)
        self.assertEqual(nxt.name, "Ripple")
        self.assertEqual(gap, 25)
        self.assertEqual(progress_to_next(950), (None, 0))


class AnswerCheckingTests(unittest.TestCase):
    def test_exact_and_numeric_forms(self):
        item = {"answers": ["36"]}
        for given in ("36", " 36 ", "36.", "36 rupees"):
            self.assertTrue(check(given, item), given)
        self.assertFalse(check("63", item))
        self.assertFalse(check("", item))

    def test_keyword_matching(self):
        item = {"answers": ["monopoly", "game"], "kind": "keyword"}
        self.assertTrue(check("he was playing MONOPOLY!", item))
        self.assertFalse(check("he ran out of petrol", item))

    def test_stress_shortens_the_clock(self):
        self.assertLess(limit_for(2, True), limit_for(2, False))
        self.assertGreater(limit_for(3, False), limit_for(1, False))


class ScoringTests(unittest.TestCase):
    def test_empty_input_is_safe(self):
        report = evaluate([])
        self.assertEqual(report.index, 0)

    def test_perfect_calm_player_scores_near_the_top(self):
        items = [attempt(correct=True, stressed=s, ratio=0.35) for s in (False, True) for _ in range(6)]
        report = evaluate(items)
        self.assertGreater(report.index, 800)
        self.assertEqual(level_for(report.index).name, "Still Water")
        self.assertGreaterEqual(report.retention, 1.0)

    def test_collapse_under_pressure_is_punished_in_calm_not_intellect(self):
        calm = [attempt(correct=True, stressed=False, ratio=0.4) for _ in range(6)]
        storm = [attempt(correct=False, stressed=True, ratio=0.9) for _ in range(6)]
        report = evaluate(calm + storm)
        self.assertGreater(report.intellect, 45)     # they can solve these
        self.assertLess(report.calm, 45)             # but not under load
        self.assertLess(report.accuracy_stress, report.accuracy_calm)

    def test_uniform_failure_is_not_treated_as_composure(self):
        """Failing equally in both phases must not read as a calm mind."""
        items = [attempt(correct=False, stressed=s, ratio=0.8) for s in (False, True) for _ in range(6)]
        report = evaluate(items)
        self.assertLess(report.calm, 40)
        self.assertLess(report.index, 250)

    def test_impulsive_wrong_answers_cost_clarity(self):
        steady = [attempt(correct=False, ratio=0.7) for _ in range(6)]
        snap = [attempt(correct=False, ratio=0.1) for _ in range(6)]
        self.assertGreater(evaluate(steady).clarity, evaluate(snap).clarity)

    def test_timeouts_are_recorded(self):
        report = evaluate([attempt(correct=False, timed_out=True, ratio=1.0) for _ in range(4)])
        self.assertEqual(report.timeout_rate, 1.0)

    def test_harder_correct_items_beat_easy_ones(self):
        easy = evaluate([attempt(correct=True, difficulty=1) for _ in range(6)])
        hard = evaluate([attempt(correct=True, difficulty=3) for _ in range(6)])
        self.assertGreaterEqual(hard.intellect, easy.intellect)

    def test_skill_breakdown(self):
        a = attempt(); a.skill = "memory"
        b = attempt(correct=False); b.skill = "logic"
        report = evaluate([a, b])
        self.assertEqual(report.skills["memory"], 100.0)
        self.assertEqual(report.skills["logic"], 0.0)

    def test_index_is_bounded(self):
        for items in ([attempt(True) for _ in range(20)], [attempt(False) for _ in range(20)]):
            self.assertTrue(0 <= evaluate(items).index <= 1000)


class ConsultationTests(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(band(20), "needs work")
        self.assertEqual(band(60), "developing")
        self.assertEqual(band(90), "strong")

    def test_low_calm_gets_the_calm_prescription_first(self):
        calm_items = [attempt(correct=True, stressed=False, ratio=0.4) for _ in range(6)]
        storm = [attempt(correct=False, stressed=True, ratio=1.0, timed_out=True) for _ in range(6)]
        picked = prescriptions(evaluate(calm_items + storm))
        self.assertEqual(picked[0].title, CALM_LOW.title)

    def test_low_intellect_gets_the_toolkit_prescription(self):
        items = [attempt(correct=False, stressed=s, ratio=0.5) for s in (False, True) for _ in range(6)]
        titles = [p.title for p in prescriptions(evaluate(items))]
        self.assertIn(INTELLECT_LOW.title, titles)

    def test_debrief_mentions_level_and_disclaimer(self):
        text = debrief(evaluate([attempt() for _ in range(6)]))
        self.assertIn("MindZen Index", text)
        self.assertIn("Zen", text)
        self.assertIn("not a clinical test", text)


class ProfileTests(unittest.TestCase):
    def test_best_index_and_trend(self):
        player = Player(name="ana")
        self.assertEqual(player.best_index, 0)
        self.assertIn("Not enough history", player.trend())
        for idx in (300, 500):
            player.sessions.append(
                Session(when="now", index=idx, intellect=1, clarity=1, calm=1,
                        accuracy=1, level=level_for(idx).name, attempts=12)
            )
        self.assertEqual(player.best_index, 500)
        self.assertIn("Up", player.trend())
        self.assertIn("[", player.history_chart())

    def test_store_roundtrip(self, ):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(directory=tmp)
            player = store.get("Ravi")
            store.record(player, evaluate([attempt() for _ in range(6)]))
            reloaded = Store(directory=tmp)
            self.assertIn("ravi", reloaded.players)
            self.assertEqual(len(reloaded.players["ravi"].sessions), 1)
            self.assertTrue(os.path.exists(os.path.join(tmp, "profiles.json")))


class ContentTests(unittest.TestCase):
    def test_every_item_is_well_formed(self):
        for game in build_games():
            items = game.items()
            self.assertTrue(items, game.name)
            for item in items:
                self.assertIn("answers", item)
                self.assertIn(item["difficulty"], (1, 2, 3))
                self.assertTrue(item["explain"])
                # the stated answer must pass its own checker
                self.assertTrue(check(item["answers"][0], item), item)


class SimulatedSessionTests(unittest.TestCase):
    def test_demo_runs_end_to_end(self):
        import io, contextlib, tempfile, os
        from mindzen.app import demo
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["MINDZEN_HOME"] = tmp
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                index = demo(seed=42, quiet=True)
        self.assertTrue(0 <= index <= 1000)
        self.assertIn("MindZen Index", buf.getvalue())

    def test_stronger_players_score_higher_on_average(self):
        import io, contextlib
        from mindzen.app import demo

        def average(skill, composure):
            scores = []
            for seed in (1, 2, 3, 4, 5, 6):
                with contextlib.redirect_stdout(io.StringIO()):
                    scores.append(demo(seed=seed, skill=skill, composure=composure, quiet=True))
            return sum(scores) / len(scores)

        self.assertLess(average(0.3, 0.25), average(0.65, 0.55))
        self.assertLess(average(0.65, 0.55), average(0.95, 0.95))


if __name__ == "__main__":
    unittest.main()
