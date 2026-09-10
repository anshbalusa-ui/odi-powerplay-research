"""Historical weather helpers for ODI match context."""

from __future__ import annotations

from statistics import fmean
from typing import Any, Iterable
from urllib.parse import urlencode


ARCHIVE_ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation",
    "cloud_cover",
    "wind_speed_10m",
)


def build_archive_url(latitude: float, longitude: float, match_date: str) -> str:
    """Build a consistent ERA5 request for one venue-date in local time."""

    query = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": match_date,
            "end_date": match_date,
            "hourly": ",".join(HOURLY_VARIABLES),
            "timezone": "auto",
            "models": "era5",
        }
    )
    return f"{ARCHIVE_ENDPOINT}?{query}"


def _numbers(values: Iterable[Any]) -> list[float]:
    return [float(value) for value in values if value is not None]


def _mean(values: Iterable[Any]) -> float | None:
    numbers = _numbers(values)
    return round(fmean(numbers), 6) if numbers else None


def _sum(values: Iterable[Any]) -> float | None:
    numbers = _numbers(values)
    return round(sum(numbers), 6) if numbers else None


def summarize_hourly_weather(payload: dict[str, Any]) -> dict[str, Any]:
    """Collapse a local-date hourly Open-Meteo response into match-day context.

    These are daily environmental covariates, not claims about the exact
    conditions during either innings. Keeping that distinction avoids false
    precision when historical innings start/end timestamps are unavailable.
    """

    hourly = payload.get("hourly") or {}
    times = list(hourly.get("time") or [])
    return {
        "weather_latitude": payload.get("latitude"),
        "weather_longitude": payload.get("longitude"),
        "weather_timezone": payload.get("timezone"),
        "weather_hours_observed": len(times),
        "temperature_2m_mean_c": _mean(hourly.get("temperature_2m") or []),
        "relative_humidity_2m_mean_pct": _mean(hourly.get("relative_humidity_2m") or []),
        "dew_point_2m_mean_c": _mean(hourly.get("dew_point_2m") or []),
        "precipitation_sum_mm": _sum(hourly.get("precipitation") or []),
        "cloud_cover_mean_pct": _mean(hourly.get("cloud_cover") or []),
        "wind_speed_10m_mean_kmh": _mean(hourly.get("wind_speed_10m") or []),
    }
