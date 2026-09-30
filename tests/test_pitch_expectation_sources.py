"""Only temporally verified article condition text can reach source reviewers."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from odi_powerplay.pitch_expectation import extract_source_candidate  # noqa: E402
from collect_pitch_expectation_candidates import acquire  # noqa: E402


class SourceExtractionTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "cricsheet_match_id": "123",
            "source_url": "https://example.org/preview",
            "source_title": "Match preview",
            "published_at_utc": "2023-04-29T12:00:00Z",
            "scheduled_start_utc": "2023-04-30T09:00:00Z",
        }
        self.html = """<html><head>
        <meta property="article:published_time" content="2023-04-29T12:00:00Z">
        <meta property="article:modified_time" content="2023-04-29T13:00:00Z">
        </head><body><nav>Live scores and winners elsewhere</nav><article>
        <p>The pitch has a little grass and could offer seam movement early.</p>
        <p>Players gathered for training.</p>
        </article></body></html>"""


    def test_focal_jsonld_article_supplies_body_and_both_timestamps(self):
        structured = """<script type="application/ld+json">{
          "@type":"NewsArticle", "url":"https://example.org/preview/",
          "datePublished":"2023-04-29T12:00:00Z",
          "dateModified":"2023-04-29T13:00:00+00:00",
          "articleBody":"The pitch has a little grass and could offer seam movement early."
        }</script>"""
        result = extract_source_candidate(self.report, structured)
        self.assertEqual(result["status"], "pre_match_candidate")
        self.assertEqual(
            result["article_published_at_utc"], "2023-04-29T12:00:00+00:00"
        )
        self.assertIn("grass", result["source_text"])

    def test_jsonld_without_focal_identity_cannot_supply_body_or_dates(self):
        structured = """<script type="application/ld+json">{
          "@type":"NewsArticle", "url":"https://example.org/other",
          "datePublished":"2023-04-29T12:00:00Z",
          "dateModified":"2023-04-29T13:00:00Z",
          "articleBody":"The pitch has a little grass and could offer seam movement early."
        }</script>"""
        result = extract_source_candidate(self.report, structured)
        self.assertEqual(result["status"], "needs_review")
        self.assertNotIn("source_text", result)

    def test_conflicting_focal_jsonld_objects_are_quarantined(self):
        item = """{"@type":"NewsArticle","url":"https://example.org/preview",
          "datePublished":"2023-04-29T12:00:00Z",
          "dateModified":"2023-04-29T13:00:00Z",
          "articleBody":"The pitch has a little grass and could offer seam movement early."}"""
        structured = (f"<script type='application/ld+json'>[{item},"
                      f"{item.replace('13:00:00Z', '14:00:00Z')}]</script>")
        result = extract_source_candidate(self.report, structured)
        self.assertEqual(result["status"], "needs_review")
        self.assertNotIn("source_text", result)

    def test_partial_structured_timestamp_is_not_accepted(self):
        structured = """<script type="application/ld+json">{
          "@type":"NewsArticle", "url":"https://example.org/preview",
          "datePublished":"2023-04-29",
          "dateModified":"2023-04-29T13:00:00Z",
          "articleBody":"The pitch has a little grass and could offer seam movement early."
        }</script>"""
        result = extract_source_candidate(self.report, structured)
        self.assertEqual(result["status"], "needs_review")
        self.assertNotIn("source_text", result)
    def test_only_article_scoped_pre_match_condition_sentence_survives(self):
        result = extract_source_candidate(self.report, self.html)
        self.assertEqual(result["status"], "pre_match_candidate")
        self.assertIn("grass", result["source_text"])
        self.assertNotIn("winners elsewhere", result["source_text"])
        self.assertNotIn("Players gathered", result["source_text"])

    def test_later_edit_or_unverified_publication_blocks_article(self):
        later = self.html.replace("2023-04-29T13:00:00Z", "2023-05-01T13:00:00Z")
        result = extract_source_candidate(self.report, later)
        self.assertEqual(result["status"], "contaminated_or_ambiguous")
        self.assertNotIn("source_text", result)
        missing = self.html.replace('property="article:modified_time"', 'name="not_modified"')
        self.assertEqual(extract_source_candidate(self.report, missing)["status"], "needs_review")
    def test_archive_capture_can_bound_missing_modification_metadata(self):
        missing = self.html.replace(
            '<meta property="article:modified_time" content="2023-04-29T13:00:00Z">',
            "",
        )
        self.assertEqual(
            extract_source_candidate(self.report, missing)["status"], "needs_review"
        )
        candidate = extract_source_candidate(
            self.report, missing, archived_at_utc="2023-04-30T08:00:00Z"
        )
        self.assertEqual(candidate["status"], "pre_match_candidate")
        self.assertIn("source_text", candidate)
        self.assertNotIn("article_modified_at_utc", candidate)

    def test_archive_timestamp_must_be_valid_and_pre_match(self):
        missing = self.html.replace(
            '<meta property="article:modified_time" content="2023-04-29T13:00:00Z">',
            "",
        )
        for timestamp in (
            "2023-04-30T09:00:00Z",
            "2023-04-30T10:00:00Z",
            "2023-04-29T11:59:59Z",
            "2023-04-30T08:00:00",
            "2023-04-30",
        ):
            with self.subTest(timestamp=timestamp):
                candidate = extract_source_candidate(
                    self.report, missing, archived_at_utc=timestamp
                )
                self.assertNotEqual(candidate["status"], "pre_match_candidate")
                self.assertNotIn("source_text", candidate)

    def test_archive_capture_rejects_embedded_modification_after_capture(self):
        candidate = extract_source_candidate(
            self.report, self.html, archived_at_utc="2023-04-29T12:30:00Z"
        )
        self.assertNotEqual(candidate["status"], "pre_match_candidate")
        self.assertNotIn("source_text", candidate)

    def test_archive_capture_rejects_modification_at_or_after_start(self):
        for modified in ("2023-04-30T09:00:00Z", "2023-05-01T09:00:00Z"):
            html = self.html.replace("2023-04-29T13:00:00Z", modified)
            candidate = extract_source_candidate(
                self.report, html, archived_at_utc="2023-04-30T08:00:00Z"
            )
            self.assertEqual(candidate["status"], "contaminated_or_ambiguous")
            self.assertNotIn("source_text", candidate)


    def test_result_text_inside_article_is_not_issued_to_reviewer(self):
        contaminated = self.html.replace("could offer seam movement early.",
                                         "could offer seam movement early. Final score 300/4.")
        result = extract_source_candidate(self.report, contaminated)
        self.assertEqual(result["status"], "contaminated_or_ambiguous")
        self.assertNotIn("source_text", result)

    def test_prior_result_sentence_is_removed_before_source_review(self):
        article = self.html.replace(
            "The pitch has a little grass and could offer seam movement early.",
            "They won their previous match. The pitch has a little grass and "
            "could offer seam movement early.",
        )
        result = extract_source_candidate(self.report, article)
        self.assertEqual(result["status"], "pre_match_candidate")
        self.assertEqual(
            result["source_text"],
            "The pitch has a little grass and could offer seam movement early.",
        )

    def test_repeated_condition_sentences_are_deduplicated_before_length_limit(self):
        sentence = "The pitch has a little grass and could offer seam movement early."
        article = self.html.replace(
            f"<p>{sentence}</p>",
            "".join(f"<p>{sentence}</p>" for _ in range(14)),
        )
        result = extract_source_candidate(self.report, article)
        self.assertEqual(result["status"], "pre_match_candidate")
        self.assertEqual(result["source_text"], sentence)

    def test_verified_domain_article_containers_exclude_navigation(self):
        cases = (
            ("https://www.sportingnews.com/in/cricket/news/example",
             '<section id="article-body"><p>{body}</p></section>'),
            ("https://www.thenews.com.pk/latest/example",
             '<div class="story-detail"><p>{body}</p></div>'),
            ("https://www.latestly.com/sports/cricket/example.html",
             '<div class="article-text"><div class="main-body"><p>{body}</p></div></div>'),
            ("https://thesportsrush.com/cricket-news-example/",
             '<div class="prose content-part"><p>{body}</p></div>'),
        )
        body = "The pitch has a little grass and could offer seam movement early."
        nav = "Navigation pitch conditions may favor batters in another match."
        for source_url, container in cases:
            with self.subTest(source_url=source_url):
                report = {**self.report, "source_url": source_url}
                article = (
                    '<meta property="article:published_time" content="2023-04-29T12:00:00Z">'
                    '<meta property="article:modified_time" content="2023-04-29T13:00:00Z">'
                    f"<nav><p>{nav}</p></nav>{container.format(body=body)}"
                )
                result = extract_source_candidate(report, article)
                self.assertEqual(result["status"], "pre_match_candidate")
                self.assertEqual(result["source_text"], body)


    def test_prior_match_scoreline_cannot_reach_assessors(self):
        contaminated = self.html.replace(
            "The pitch has a little grass",
            "After a 300-run total last match, the pitch has a little grass",
        )
        result = extract_source_candidate(self.report, contaminated)
        self.assertEqual(result["status"], "contaminated_or_ambiguous")
        self.assertNotIn("source_text", result)

    def test_plural_prior_defeats_cannot_share_a_condition_sentence(self):
        contaminated = self.html.replace(
            "The pitch has a little grass",
            "Following two defeats, the pitch has a little grass",
        )
        result = extract_source_candidate(self.report, contaminated)
        self.assertEqual(result["status"], "contaminated_or_ambiguous")
        self.assertNotIn("source_text", result)


    def test_past_chase_stat_and_empty_heading_are_not_released(self):
        scored = self.html.replace(
            "The pitch has a little grass",
            "A comfortable chase of 281 showed the pitch has a little grass",
        )
        self.assertEqual(extract_source_candidate(self.report, scored)["status"],
                         "contaminated_or_ambiguous")
        heading = self.html.replace(
            "The pitch has a little grass and could offer seam movement early.", "Conditions"
        )
        self.assertEqual(extract_source_candidate(self.report, heading)["status"], "needs_review")

    def test_prior_result_in_title_blocks_source_before_review(self):
        report = {**self.report, "source_title": "Series conceded before next match"}
        result = extract_source_candidate(report, self.html)
        self.assertEqual(result["status"], "contaminated_or_ambiguous")
        self.assertNotIn("source_text", result)

    def test_cached_snapshot_cannot_be_reused_for_different_source_url(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            body = self.html.encode()
            (raw / "123.saved.html").write_bytes(body)
            (raw / "123.saved.json").write_text(json.dumps({
                "cricsheet_match_id": "123",
                "source_url": "https://example.org/other-preview",
                "snapshot_filename": "123.saved.html",
                "raw_sha256": hashlib.sha256(body).hexdigest(),
                "retrieved_at_utc": "2026-09-28T07:00:00+00:00",
                "http_status": "200", "curl_exit_status": 0,
            }))
            with self.assertRaises(ValueError):
                acquire(self.report, raw)

    def test_sidebar_result_and_related_story_cannot_contaminate_or_supply_evidence(self):
        outside = self.html.replace(
            "</article>",
            "</article><aside><p>Final score 300/4, the pitch favored batters.</p>"
            "<article class='related-story'><p>The pitch was slow and dusty with "
            "turn for spinners throughout the match.</p></article></aside>",
        )
        result = extract_source_candidate(self.report, outside)
        self.assertEqual(result["status"], "pre_match_candidate")
        self.assertEqual(
            result["source_text"],
            "The pitch has a little grass and could offer seam movement early.",
        )

    def test_result_or_live_marker_inside_focal_article_quarantines_source(self):
        for marker in ("Live score 120/2.", "They won by 5 wickets."):
            with self.subTest(marker=marker):
                contaminated = self.html.replace("</article>", f"<p>{marker}</p></article>")
                result = extract_source_candidate(self.report, contaminated)
                self.assertEqual(result["status"], "contaminated_or_ambiguous")
                self.assertNotIn("source_text", result)

    def test_weak_or_empty_focal_article_evidence_is_not_released(self):
        weak = self.html.replace(
            "The pitch has a little grass and could offer seam movement early.",
            "The pitch looks green.",
        )
        empty = self.html.replace(
            "The pitch has a little grass and could offer seam movement early.",
            "",
        )
        self.assertEqual(extract_source_candidate(self.report, weak)["status"], "needs_review")
        self.assertEqual(extract_source_candidate(self.report, empty)["status"], "needs_review")
    def test_unrelated_article_paragraph_cannot_supply_conditions(self):
        irrelevant = self.html.replace("The pitch has a little grass and could offer seam movement early.",
                                       "The teams trained at the ground.")
        self.assertEqual(extract_source_candidate(self.report, irrelevant)["status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
