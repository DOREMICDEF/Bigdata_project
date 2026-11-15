import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import initial_level, recommend, summarize, validate_record


def sample(experience="sometimes", correct=6, extra=False):
    level = initial_level(experience)
    cycle = {1: [0, 1], 2: [0, 1, 2], 3: [0, 0, 1]}[level]
    limit = {1: 40000, 2: 35000, 3: 30000}[level] * (1.5 if extra else 1)
    return {"schema_version": "1.0", "stage": 1, "participant_id": "test_person_01",
            "round_id": "test_round_01", "completed_at": "2026-11-10T01:00:00Z",
            "retry_count": 0, "recording_consent": True, "initial_level": level,
            "profile": {"experience": experience, "age_group": "unspecified", "disability": "unspecified",
                        "demographic_consent": False, "large_text": False, "extra_time": extra},
            "questions": [{"question_index": i+1, "level": level, "cycle": cycle,
                           "sequence": cycle*2, "selected": 0 if i < correct else 3,
                           "outcome": "answer", "response_ms": 10000, "limit_ms": limit,
                           "hint_used": False} for i in range(6)]}


class CoreTests(unittest.TestCase):
    def test_upgrade(self):
        self.assertEqual(recommend(sample())["next_level"], 3)

    def test_variable_sequence_end(self):
        record = sample()
        record["questions"][0].update(sequence=[0,1,2,0,1,2,0], selected=1)
        self.assertEqual(summarize(record)["correct_count"], 6)

    def test_downgrade(self):
        self.assertEqual(recommend(sample(correct=2))["next_level"], 1)

    def test_keep(self):
        self.assertEqual(recommend(sample(correct=4))["next_level"], 2)

    def test_boundaries(self):
        self.assertEqual(recommend(sample("new", 0))["next_level"], 1)
        self.assertEqual(recommend(sample("often"))["next_level"], 3)

    def test_no_demographic_penalty(self):
        record = sample()
        a = recommend(record)
        record["profile"].update(age_group="65plus", disability="yes", demographic_consent=True)
        self.assertEqual(a, recommend(record))

    def test_accessibility_does_not_reduce_recommendation(self):
        self.assertEqual(recommend(sample())["next_level"], recommend(sample(extra=True))["next_level"])
        self.assertEqual(recommend(sample(extra=True))["next_seconds"], 45)

    def test_timeout_rule(self):
        record = sample()
        for q in record["questions"][:2]:
            q.update(outcome="timeout", selected=None, response_ms=q["limit_ms"])
        self.assertEqual(recommend(record)["next_level"], 1)
        self.assertEqual(summarize(record)["timeout_count"], 2)

    def test_hint_and_speed_prevent_upgrade(self):
        record = sample()
        for q in record["questions"][:2]:
            q["hint_used"] = True
        self.assertEqual(recommend(record)["next_level"], 2)
        for q in record["questions"]:
            q.update(hint_used=False, response_ms=30000)
        self.assertEqual(recommend(record)["next_level"], 2)

    def test_recalculate_instead_of_trusting_scores(self):
        record = sample(correct=0)
        for q in record["questions"]:
            q.update(correct=True, correct_answer=3)
        self.assertEqual(summarize(record)["correct_count"], 0)

    def test_reject_invalid_inputs(self):
        mutations = [lambda r: r.update(stage=2), lambda r: r.update(recording_consent=False),
                     lambda r: r["questions"].pop(), lambda r: r["questions"][0].update(response_ms=float("nan")),
                     lambda r: r["questions"][0].update(response_ms=-1),
                     lambda r: r["questions"][0].update(outcome="timeout"),
                     lambda r: r["questions"][0].update(cycle=[0,0,0]),
                     lambda r: r["questions"][0].update(sequence=[0,1]),
                     lambda r: r["profile"].update(disability="yes"),
                     lambda r: r["questions"][0].update(response_ms=35000),
                     lambda r: r["questions"][0].update(limit_ms=100000),
                     lambda r: r.update(initial_level=True),
                     lambda r: r.update(completed_at="yesterday")]
        for mutate in mutations:
            record = sample()
            mutate(record)
            with self.subTest(record=record), self.assertRaises(ValueError):
                validate_record(record)

    def test_skip(self):
        record = sample()
        record["questions"][0].update(selected=None, outcome="skip")
        self.assertEqual(summarize(record)["skip_count"], 1)
        self.assertEqual(summarize(record)["correct_count"], 5)

    def test_unknown_fields_stripped(self):
        record = sample()
        record["name"] = "should not persist"
        record["profile"]["phone"] = "should not persist"
        result = validate_record(record)
        self.assertNotIn("name", result)
        self.assertNotIn("phone", result["profile"])

    def test_json_roundtrip(self):
        record = validate_record(sample())
        self.assertEqual(record, validate_record(json.loads(json.dumps(record))))


if __name__ == "__main__":
    unittest.main()
