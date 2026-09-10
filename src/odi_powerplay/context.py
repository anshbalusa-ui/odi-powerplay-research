"""Strict match-level context joins for the ODI powerplay analysis table."""

from __future__ import annotations

from typing import Any, Iterable


PITCH_CONTEXT_COLUMNS = (
    "source_url",
    "source_title",
    "published_at_utc",
    "coder_confidence",
    "pitch_primary_category",
    "batting_ease",
    "pace_seam_support",
    "spin_support",
    "bounce_profile",
    "two_paced_expected",
    "dew_expected",
)

WEATHER_CONTEXT_COLUMNS = (
    "weather_status",
    "weather_window",
    "weather_model",
    "weather_source_url",
    "weather_timezone",
    "weather_hours_observed",
    "temperature_2m_mean_c",
    "relative_humidity_2m_mean_pct",
    "dew_point_2m_mean_c",
    "precipitation_sum_mm",
    "cloud_cover_mean_pct",
    "wind_speed_10m_mean_kmh",
    "geocode_name",
    "geocode_country",
)


def _truthy_one(value: Any) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "y"}


def _unique_index(
    rows: Iterable[dict[str, Any]], *, key: str, label: str
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        match_id = str(row.get(key) or "").strip()
        if not match_id:
            continue
        if match_id in index:
            raise ValueError(f"Duplicate {label} row for match {match_id}")
        index[match_id] = row
    return index


def merge_context(
    innings_rows: Iterable[dict[str, Any]],
    *,
    pitch_rows: Iterable[dict[str, Any]],
    weather_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach only verified pre-match pitch data and successful weather context.

    The function never multiplies innings rows. Match-level source records must
    be unique, and unverified pitch records are treated as missing context.
    """

    pitch_index = _unique_index(pitch_rows, key="cricsheet_match_id", label="pitch")
    weather_index = _unique_index(weather_rows, key="match_id", label="weather")

    merged: list[dict[str, Any]] = []
    for raw in innings_rows:
        row = dict(raw)
        match_id = str(row["match_id"])

        pitch = pitch_index.get(match_id)
        pitch_available = bool(pitch and _truthy_one(pitch.get("pre_match_verified")))
        row["pitch_available"] = int(pitch_available)
        if pitch_available and pitch is not None:
            for column in PITCH_CONTEXT_COLUMNS:
                if column in pitch:
                    row[column] = pitch[column]

        weather = weather_index.get(match_id)
        weather_available = bool(weather and str(weather.get("weather_status")) == "ok")
        row["weather_available"] = int(weather_available)
        if weather_available and weather is not None:
            for column in WEATHER_CONTEXT_COLUMNS:
                if column in weather:
                    row[column] = weather[column]

        merged.append(row)

    return merged
