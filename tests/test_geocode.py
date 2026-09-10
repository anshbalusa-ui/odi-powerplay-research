from __future__ import annotations

import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.geocode import (  # noqa: E402
    build_geocoding_url,
    choose_candidate,
    geocode_query,
    unique_geocode_queries,
)


class GeocodeTests(unittest.TestCase):
    def test_known_city_is_preferred_over_venue_name(self) -> None:
        self.assertEqual(geocode_query("Lord's", "London"), "London")
        self.assertEqual(
            geocode_query("Melbourne Cricket Ground", "Unknown"),
            "Melbourne Cricket Ground",
        )

    def test_geocoding_url_is_auditable_and_requests_multiple_candidates(self) -> None:
        parsed = urlparse(build_geocoding_url("Colombo"))
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "geocoding-api.open-meteo.com")
        self.assertEqual(query["name"], ["Colombo"])
        self.assertEqual(query["count"], ["5"])
        self.assertEqual(query["language"], ["en"])
        self.assertEqual(query["format"], ["json"])

    def test_unique_city_name_candidate_can_be_auto_accepted(self) -> None:
        payload = {
            "results": [
                {
                    "id": 1,
                    "name": "Colombo",
                    "latitude": 6.9355,
                    "longitude": 79.8487,
                    "country": "Sri Lanka",
                    "country_code": "LK",
                    "timezone": "Asia/Colombo",
                    "population": 648034,
                },
                {
                    "id": 2,
                    "name": "Colombo District",
                    "latitude": 6.9,
                    "longitude": 80.0,
                    "country": "Sri Lanka",
                    "country_code": "LK",
                    "timezone": "Asia/Colombo",
                },
            ]
        }
        chosen = choose_candidate(payload, "Colombo")
        self.assertEqual(chosen["geocode_name"], "Colombo")
        self.assertEqual(chosen["latitude"], 6.9355)
        self.assertEqual(chosen["longitude"], 79.8487)
        self.assertEqual(chosen["timezone"], "Asia/Colombo")
        self.assertEqual(chosen["geocode_auto_match"], 1)

    def test_ambiguous_or_missing_candidate_is_flagged_for_review(self) -> None:
        ambiguous = {
            "results": [
                {"name": "Kingston", "latitude": 17.9, "longitude": -76.8, "country": "Jamaica"},
                {"name": "Kingston", "latitude": 44.2, "longitude": -76.5, "country": "Canada"},
            ]
        }
        self.assertEqual(choose_candidate(ambiguous, "Kingston")["geocode_auto_match"], 0)
        self.assertEqual(choose_candidate({}, "Nowhere")["geocode_status"], "no_result")

    def test_duplicate_city_queries_are_requested_only_once(self) -> None:
        venue_rows = [
            {"venue": "Lord's", "city": "London"},
            {"venue": "The Oval", "city": "London"},
            {"venue": "Sydney Cricket Ground", "city": "Unknown"},
        ]
        self.assertEqual(
            unique_geocode_queries(venue_rows),
            ["London", "Sydney Cricket Ground"],
        )


if __name__ == "__main__":
    unittest.main()
