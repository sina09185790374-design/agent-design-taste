"""Real tests for agent-design-taste — all must pass."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_design_taste import audit_html, exit_code_for, format_report  # noqa: E402
from main import DEMO_GOOD, DEMO_BAD, main  # noqa: E402

GOOD = DEMO_GOOD
BAD = DEMO_BAD


def status_of(result, check):
    for f in result.findings:
        if f.check == check:
            return f.status
    raise AssertionError(f"check {check} not found")


class TestBasics(unittest.TestCase):
    def test_good_scores_pass(self):
        r = audit_html(GOOD)
        self.assertEqual(r.verdict, "PASS")
        self.assertGreaterEqual(r.score, 80)

    def test_bad_scores_sloppy(self):
        r = audit_html(BAD)
        self.assertEqual(r.verdict, "SLOPPY")
        self.assertLess(r.score, 60)

    def test_exit_codes(self):
        self.assertEqual(exit_code_for("PASS"), 0)
        self.assertEqual(exit_code_for("NEEDS_WORK"), 1)
        self.assertEqual(exit_code_for("SLOPPY"), 2)

    def test_report_mentions_score(self):
        r = audit_html(GOOD)
        self.assertIn("Score:", format_report(r, "x.html"))

    def test_json_shape(self):
        r = audit_html(GOOD)
        d = r.to_dict()
        self.assertIn("score", d)
        self.assertIn("verdict", d)
        self.assertTrue(all("check" in f and "status" in f for f in d["findings"]))


class TestDocumentChecks(unittest.TestCase):
    def test_placeholder_title_fails(self):
        r = audit_html("<html><head><title>Document</title></head><body><h1>x</h1></body></html>")
        self.assertEqual(status_of(r, "title_tag"), "fail")

    def test_missing_title_fails(self):
        r = audit_html("<html><head></head><body><h1>x</h1></body></html>")
        self.assertEqual(status_of(r, "title_tag"), "fail")

    def test_missing_viewport_fails(self):
        r = audit_html(
            "<html lang='en'><head><title>Real title here</title></head>"
            "<body><h1>x</h1></body></html>"
        )
        self.assertEqual(status_of(r, "viewport_meta"), "fail")

    def test_missing_lang_warns(self):
        r = audit_html(
            "<html><head><title>Real title here</title>"
            "<meta name='viewport' content='width=device-width'></head>"
            "<body><h1>x</h1></body></html>"
        )
        self.assertEqual(status_of(r, "lang_attr"), "warn")

    def test_multiple_h1_warns(self):
        r = audit_html(
            "<html><head><title>Real title here</title></head>"
            "<body><h1>a</h1><h1>b</h1></body></html>"
        )
        self.assertEqual(status_of(r, "heading_structure"), "warn")

    def test_missing_h1_fails(self):
        r = audit_html(
            "<html><head><title>Real title here</title></head>"
            "<body><p>no heading</p></body></html>"
        )
        self.assertEqual(status_of(r, "heading_structure"), "fail")

    def test_semantic_tags_pass(self):
        r = audit_html(GOOD)
        self.assertEqual(status_of(r, "semantic_html"), "pass")


class TestImageChecks(unittest.TestCase):
    def test_missing_alt_fails(self):
        r = audit_html(
            "<html><head><title>Real title here</title></head>"
            "<body><h1>x</h1><img src='a.jpg'></body></html>"
        )
        self.assertEqual(status_of(r, "img_alt"), "fail")

    def test_placeholder_host_fails(self):
        r = audit_html(
            "<html><head><title>Real title here</title></head>"
            "<body><h1>x</h1>"
            "<img src='https://picsum.photos/200' alt='x'></body></html>"
        )
        self.assertEqual(status_of(r, "placeholder_images"), "fail")

    def test_good_alt_passes(self):
        r = audit_html(GOOD)
        self.assertEqual(status_of(r, "img_alt"), "pass")


class TestTasteChecks(unittest.TestCase):
    def test_slop_gradient_warns(self):
        r = audit_html(BAD)
        self.assertEqual(status_of(r, "generic_gradient"), "warn")

    def test_emoji_in_ui_warns(self):
        r = audit_html(BAD)
        self.assertEqual(status_of(r, "emoji_in_ui"), "warn")

    def test_cliche_headings_warn(self):
        r = audit_html(BAD)
        self.assertEqual(status_of(r, "cliche_headings"), "warn")

    def test_ai_phrases_warn(self):
        r = audit_html(BAD)
        self.assertEqual(status_of(r, "ai_phrases"), "warn")

    def test_generic_buttons_warn(self):
        r = audit_html(BAD)
        self.assertEqual(status_of(r, "generic_buttons"), "warn")

    def test_lorem_fails(self):
        r = audit_html(BAD)
        self.assertEqual(status_of(r, "lorem"), "fail")

    def test_specific_copy_passes(self):
        r = audit_html(GOOD)
        for check in ("cliche_headings", "ai_phrases", "generic_buttons", "lorem"):
            self.assertEqual(status_of(r, check), "pass", check)

    def test_css_variables_pass(self):
        r = audit_html(GOOD)
        self.assertEqual(status_of(r, "design_tokens"), "pass")


class TestCLI(unittest.TestCase):
    def test_demo_runs(self):
        code = main(["--demo"])
        # demo includes the bad sample, so worst must be SLOPPY (2)
        self.assertEqual(code, 2)

    def test_demo_json_runs(self):
        code = main(["--demo", "--json"])
        self.assertEqual(code, 2)

    def test_good_file_passes(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(GOOD)
            path = fh.name
        try:
            self.assertEqual(main([path]), 0)
        finally:
            os.unlink(path)

    def test_missing_file_errors(self):
        self.assertEqual(main(["/nonexistent/xyz.html"]), 3)


if __name__ == "__main__":
    unittest.main()
