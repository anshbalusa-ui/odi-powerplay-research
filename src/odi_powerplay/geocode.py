"""Auditable geocoding helpers for cricket venues."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode


GEOCODING_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"


def geocode_query(venue: str, city: str | None) -> str:
    """Return the least-ambiguous available search term without inventing location data."""

    normalized_city = str(city or "").strip()
    if normalized_city and normalized_city.lower() != "unknown":
        return normalized_city
    return str(venue).strip()


def build_geocoding_url(query: str) -> str:
    """Build a stable Open-Meteo geocoding request returning several candidates."""

    params = urlencode({"name": query, "count": 5, "language": "en", "format": "json"})
    return f"{GEOCODING_ENDPOINT}?{params}"


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _candidate_record(candidate: dict[str, Any], *, auto_match: int, status: str) -> dict[str, Any]:
    return {
        "geocode_status": status,
        "geocode_auto_match": auto_match,
        "geocode_id": candidate.get("id"),
        "geocode_name": candidate.get("name"),
        "geocode_admin1": candidate.get("admin1"),
        "geocode_country": candidate.get("country"),
        "geocode_country_code": candidate.get("country_code"),
        "latitude": candidate.get("latitude"),
        "longitude": candidate.get("longitude"),
        "timezone": candidate.get("timezone"),
    }


def choose_candidate(payload: dict[str, Any], query: str) -> dict[str, Any]:
    """Choose an unambiguous exact-name location or flag the query for review.

    Exact-name auto-acceptance is intentionally conservative. If multiple exact
    matches exist (for example Kingston in different countries), the first
    candidate is retained only as a review suggestion and is not auto-accepted.
    """

    results = list(payload.get("results") or [])
    if not results:
        return {
            "geocode_status": "no_result",
            "geocode_auto_match": 0,
            "geocode_id": None,
            "geocode_name": None,
            "geocode_admin1": None,
            "geocode_country": None,
            "geocode_country_code": None,
            "latitude": None,
            "longitude": None,
            "timezone": None,
        }

    exact = [candidate for candidate in results if _normalized(candidate.get("name")) == _normalized(query)]
    if len(exact) == 1:
        return _candidate_record(exact[0], auto_match=1, status="auto_exact_name")

    suggestion = exact[0] if exact else results[0]
    return _candidate_record(suggestion, auto_match=0, status="needs_review")
