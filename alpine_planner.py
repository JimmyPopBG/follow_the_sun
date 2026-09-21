from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Iterable, List


FITNESS_ORDER = {"easy": 1, "moderate": 2, "hard": 3}


@dataclass(frozen=True)
class WeatherForecast:
    area: str
    condition: str
    precipitation_mm: float
    wind_kmh: float
    visibility_km: float


@dataclass(frozen=True)
class Tour:
    name: str
    area: str
    sport: str
    fitness_level: str
    source: str


class DAVWeatherClient:
    """Lightweight DAV-like weather source wrapper.

    The constructor accepts pre-fetched forecast dicts so this can be used
    without API credentials while still matching a real provider flow.
    """

    def __init__(self, forecasts: Iterable[dict]):
        self._forecasts = list(forecasts)

    def get_forecasts(self) -> List[WeatherForecast]:
        return [WeatherForecast(**item) for item in self._forecasts]


class KomootToursClient:
    """Lightweight Komoot-like tours source wrapper."""

    def __init__(self, tours: Iterable[dict]):
        self._tours = list(tours)

    def get_tours(self) -> List[Tour]:
        return [Tour(**item) for item in self._tours]


def has_robust_good_weather(forecast: WeatherForecast) -> bool:
    """Conservative alpine weather check for safer tour planning.

    Rules:
    - only "sunny" or "partly_cloudy"
    - very low precipitation (<= 1.0 mm)
    - manageable wind (<= 30 km/h)
    - enough visibility (>= 8 km)
    """

    condition = forecast.condition.strip().lower()
    return (
        condition in {"sunny", "partly_cloudy"}
        and forecast.precipitation_mm <= 1.0
        and forecast.wind_kmh <= 30
        and forecast.visibility_km >= 8
    )


def can_group_do_tour(group_fitness: str, tour_fitness: str) -> bool:
    group_rank = FITNESS_ORDER.get(group_fitness.strip().lower())
    tour_rank = FITNESS_ORDER.get(tour_fitness.strip().lower())
    if not group_rank or not tour_rank:
        return False
    return group_rank >= tour_rank


def recommend_tours(
    forecasts: Iterable[WeatherForecast],
    tours: Iterable[Tour],
    sport: str,
    group_fitness: str,
) -> List[Tour]:
    good_areas = {f.area.strip().lower() for f in forecasts if has_robust_good_weather(f)}
    target_sport = sport.strip().lower()
    results = [
        t
        for t in tours
        if t.sport.strip().lower() == target_sport
        and t.area.strip().lower() in good_areas
        and can_group_do_tour(group_fitness, t.fitness_level)
    ]
    return sorted(results, key=lambda t: (FITNESS_ORDER.get(t.fitness_level.lower(), 99), t.name))


def _load_json(path: str, required_keys: set[str] | None = None, string_keys: set[str] | None = None):
    """Load a JSON array of objects matching WeatherForecast/Tour fields."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("Input JSON must be a list of objects.")
    if required_keys:
        for index, item in enumerate(data):
            missing = required_keys - set(item.keys())
            if missing:
                raise ValueError(f"Record {index} is missing required fields: {sorted(missing)}")
    if string_keys:
        for index, item in enumerate(data):
            for key in string_keys:
                if key in item and not isinstance(item[key], str):
                    raise TypeError(f"Record {index} field '{key}' must be a string.")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alpine weather + tour planning helper")
    parser.add_argument("--sport", choices=["hiking", "skiing", "mountaineering"], required=True)
    parser.add_argument("--fitness", choices=["easy", "moderate", "hard"], required=True)
    parser.add_argument("--weather-json", required=True, help="Path to DAV-style forecast JSON list")
    parser.add_argument("--tours-json", required=True, help="Path to Komoot-style tours JSON list")
    return parser


def main() -> int:
    parser = build_parser()
    try:
        args = parser.parse_args()
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return code

    try:
        weather_client = DAVWeatherClient(
            _load_json(
                args.weather_json,
                required_keys={"area", "condition", "precipitation_mm", "wind_kmh", "visibility_km"},
                string_keys={"area", "condition"},
            )
        )
        tours_client = KomootToursClient(
            _load_json(
                args.tours_json,
                required_keys={"name", "area", "sport", "fitness_level", "source"},
                string_keys={"name", "area", "sport", "fitness_level", "source"},
            )
        )
        recommendations = recommend_tours(
            forecasts=weather_client.get_forecasts(),
            tours=tours_client.get_tours(),
            sport=args.sport,
            group_fitness=args.fitness,
        )
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 1

    if not recommendations:
        print("No robust-weather tours found for this sport/fitness combination.")
        return 0

    for tour in recommendations:
        print(f"{tour.name} | {tour.area} | {tour.sport} | {tour.fitness_level} | {tour.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
