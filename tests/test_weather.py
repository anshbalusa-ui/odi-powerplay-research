from __future__ import annotations

import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from odi_powerplay.weather import build_archive_url, summarize_hourly_weather  # noqa: E402


class WeatherTests(unittest.TestCase):
    def test_archive_url_uses_consistent_era5_and_expected_variables(self) -> None:
        url = build_archive_url(51.5074, -0.1278, "2023-09-08")
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.netloc, "archive-api.open-meteo.com")
        self.assertEqual(query["start_date"], ["2023-09-08"])
        self.assertEqual(query["end_date"], ["2023-09-08"])
        self.assertEqual(query["timezone"], ["auto"])
        self.assertEqual(query["models"], ["era5"])
        self.assertEqual(
            query["hourly"][0].split(","),
            [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "precipitation",
                "cloud_cover",
                "wind_speed_10m",
            ],
        )

    def test_hourly_values_are_summarized_without_false_precision(self) -> None:
        payload = {
            "latitude": 51.5,
            "longitude": -0.1,
            "timezone": "Europe/London",
            "hourly": {
                "time": ["2023-09-08T00:00", "2023-09-08T01:00", "2023-09-08T02:00"],
                "temperature_2m": [20.0, 22.0, None],
                "relative_humidity_2m": [60.0, 70.0, 80.0],
                "dew_point_2m": [12.0, 14.0, 16.0],
                "precipitation": [0.0, 1.5, 0.5],
                "cloud_cover": [10.0, 20.0, 30.0],
                "wind_speed_10m": [5.0, 7.0, 9.0],
            },
        }

        summary = summarize_hourly_weather(payload)

        self.assertEqual(summary["weather_timezone"], "Europe/London")
        self.assertEqual(summary["weather_hours_observed"], 3)
        self.assertAlmostEqual(summary["temperature_2m_mean_c"], 21.0)
        self.assertAlmostEqual(summary["relative_humidity_2m_mean_pct"], 70.0)
        self.assertAlmostEqual(summary["dew_point_2m_mean_c"], 14.0)
        self.assertAlmostEqual(summary["precipitation_sum_mm"], 2.0)
        self.assertAlmostEqual(summary["cloud_cover_mean_pct"], 20.0)
        self.assertAlmostEqual(summary["wind_speed_10m_mean_kmh"], 7.0)


if __name__ == "__main__":
    unittest.main()
