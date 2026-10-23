#!/usr/bin/env python3
"""Regression tests for observable coverage and reference failures."""
import copy
import unittest
from audit_curriculum import audit


def fixture():
    citation = [{"source": "s1", "page": 1}]
    check = {"prompt": "Which event starts the timer?", "options": ["Sending", "Waiting"],
             "answer": 0, "option_feedback": ["The timer starts when sending.", "Waiting does not create a new timer."]}
    q = {"id": "l1", "mode": "learn", "chapter": "c1", "topics": ["t1"], "family": "timer",
         "difficulty": "foundation", "tier": "core", "kind": "choice", "grading": "auto",
         "prompt": check["prompt"], "options": check["options"], "answer": 0,
         "option_feedback": check["option_feedback"], "explanation": "Start with the send event.",
         "basis": "course", "citations": citation}
    r1 = dict(q, id="r1", mode="review", family="timer-recall")
    r2 = dict(q, id="r2", mode="review", family="timer-transfer", difficulty="challenge")
    return {"schema_version": 1, "course": "Test course",
            "materials": {"slides": "provided", "papers": "none", "scope_basis": "One supplied lecture"},
            "sources": [{"id": "s1", "kind": "slides", "locator": "lecture.pdf", "pages": 2}],
            "chapters": [{"id": "c1", "priority_reason": "Core prerequisite"}],
            "topics": [{"id": "t1", "title": "Timer", "chapter": "c1", "core": True,
                        "prerequisites": [], "citations": citation}],
            "lessons": [{"id": "ll1", "mode": "learn", "topics": ["t1"], "body": "Trace one event.",
                         "example": "Send at zero, timeout at three.", "classroom_check": check},
                        {"id": "rl1", "mode": "review", "topics": ["t1"], "body": "Recall the trigger.",
                         "recall_prompt": "When does timing start?", "conditions": "This simplified sender model."}],
            "questions": [q, r1, r2]}


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(fixture())

    def rejected(self, fragment):
        result = audit(self.data)
        self.assertFalse(result["ok"])
        self.assertTrue(any(fragment in e for e in result["errors"]), result)

    def test_valid_counts_are_derived(self):
        result = audit(self.data)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["counts"]["by_chapter"]["c1"], {"learn": 1, "review": 2})
        self.assertEqual(result["counts"]["review_families"], 2)

    def test_duplicate_question_id(self):
        self.data["questions"][1]["id"] = "l1"
        self.rejected("duplicate id")

    def test_missing_review_coverage(self):
        for q in self.data["questions"][1:]:
            q["tier"] = "optional"
        self.rejected("missing review core question")

    def test_missing_classroom_feedback(self):
        self.data["lessons"][0]["classroom_check"]["option_feedback"] = ["Only one explanation"]
        self.rejected("every option requires feedback")

    def test_cycle(self):
        self.data["topics"][0]["prerequisites"] = ["t1"]
        self.rejected("prerequisite cycle")

    def test_unknown_prerequisite(self):
        self.data["topics"][0]["prerequisites"] = ["missing"]
        self.rejected("unknown prerequisite")

    def test_page_out_of_range(self):
        self.data["topics"][0]["citations"] = [{"source": "s1", "page": 3}]
        self.rejected("page outside")

    def test_paper_claim_without_paper(self):
        self.data["questions"][0]["basis"] = "paper"
        self.rejected("paper claim lacks paper/sample citation")

    def test_unknown_material_status(self):
        self.data["materials"]["papers"] = "unknown"
        self.rejected("explicitly confirm")

    def test_self_grading_needs_rubric(self):
        self.data["questions"][2]["grading"] = "self"
        self.rejected("missing rubric")

    def test_web_source_uses_section(self):
        self.data["sources"][0] = {"id": "s1", "kind": "official", "locator": "https://example.org/course"}
        self.data["materials"]["slides"] = "none"
        self.rejected("non-paged source requires section")
        for topic in self.data["topics"]:
            topic["citations"] = [{"source": "s1", "section": "Timers"}]
        for q in self.data["questions"]:
            q["citations"] = [{"source": "s1", "section": "Timers"}]
        self.assertTrue(audit(self.data)["ok"])

    def test_root_type(self):
        self.assertFalse(audit([])["ok"])

    def test_empty_reference_answer(self):
        self.data["questions"][0]["answer"] = []
        self.rejected("missing reference answer")

    def test_numeric_zero_is_valid_answer(self):
        self.data["questions"][0].update(kind="numeric", answer=0)
        self.assertTrue(audit(self.data)["ok"])


if __name__ == "__main__":
    unittest.main()
