"""Tests for scripts/check_brief.py. Run with: python -m unittest discover -s tests -v"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_brief  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "issues-2026-w46.json"
BRIEF = ROOT / "briefs" / "2026-w46-cpo-brief.md"


class CheckBriefTests(unittest.TestCase):
    def setUp(self):
        self.issues = check_brief.load_issues_json(FIXTURE)
        self.brief = BRIEF.read_text(encoding="utf-8")

    def run_check(self, text, issues=None):
        return check_brief.check(text, "brief.md", issues or self.issues)

    def test_current_brief_passes_against_its_snapshot(self):
        report = self.run_check(self.brief)
        self.assertEqual(report.errors, [])

    def test_reads_owner_from_issue_form(self):
        self.assertEqual(self.issues[2].owner, "People Operations lead")
        self.assertFalse(self.issues[5].has_owner)

    def test_bullet_without_citation_fails(self):
        report = self.run_check(self.brief + "\n- An uncited claim about morale.\n")
        self.assertTrue(any("no issue citation" in e for e in report.errors))

    def test_citing_a_closed_issue_fails(self):
        issues = dict(self.issues)
        issues[4] = check_brief.Issue(4, issues[4].title, "closed", issues[4].body)
        report = self.run_check(self.brief, issues)
        self.assertTrue(any(e.startswith("#4 ") and "closed" in e for e in report.errors))

    def test_citing_a_missing_issue_fails(self):
        report = self.run_check(self.brief + "\n- Something new. [#999]\n")
        self.assertIn("#999 is cited but does not exist.", report.errors)

    def test_owner_gap_missing_from_note_fails(self):
        line = next(l for l in self.brief.splitlines() if l.startswith("**Owner gaps"))
        text = self.brief.replace(line, "**Owner gaps to resolve:** #8 has no owner.")
        report = self.run_check(text)
        self.assertTrue(any(e.startswith("#5 ") and "owner-gap note" in e for e in report.errors))

    def test_filled_owner_is_noted_not_failed(self):
        issues = dict(self.issues)
        body = issues[8].body.replace("_No response_", "Employee Listening lead", 1)
        issues[8] = check_brief.Issue(8, issues[8].title, "open", body)
        report = self.run_check(self.brief, issues)
        self.assertEqual(report.errors, [])
        self.assertTrue(any("#8 is in the owner-gap note but now has an owner" in n for n in report.notes))

    def test_uncited_open_issue_is_a_note(self):
        issues = dict(self.issues)
        issues[20] = check_brief.Issue(20, "[Signal]: New thing", "open", "### Owner\n\nTalent lead\n")
        report = self.run_check(self.brief, issues)
        self.assertEqual(report.errors, [])
        self.assertTrue(any(n.startswith("#20 ") for n in report.notes))


if __name__ == "__main__":
    unittest.main()
