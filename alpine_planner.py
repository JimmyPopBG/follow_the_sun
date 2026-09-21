from __future__ import annotations

import argparse
import json
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

    return (
        forecast.condition in {"sunny", "partly_cloudy"}
        and forecast.precipitation_mm <= 1.0
        and forecast.wind_kmh <= 30
        and forecast.visibility_km >= 8
    )


def can_group_do_tour(group_fitness: str, tour_fitness: str) -> bool:
    group_rank = FITNESS_ORDER.get(group_fitness)
    tour_rank = FITNESS_ORDER.get(tour_fitness)
    if not group_rank or not tour_rank:
        return False
    return group_rank >= tour_rank


def recommend_tours(
    forecasts: Iterable[WeatherForecast],
    tours: Iterable[Tour],
    sport: str,
    group_fitness: str,
) -> List[Tour]:
    good_areas = {f.area for f in forecasts if has_robust_good_weather(f)}
    results = [
        t
        for t in tours
        if t.sport == sport
        and t.area in good_areas
        and can_group_do_tour(group_fitness, t.fitness_level)
    ]
    return sorted(results, key=lambda t: (FITNESS_ORDER[t.fitness_level], t.name))


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alpine weather + tour planning helper")
    parser.add_argument("--sport", choices=["hiking", "skiing", "mountaineering"], required=True)
    parser.add_argument("--fitness", choices=["easy", "moderate", "hard"], required=True)
    parser.add_argument("--weather-json", required=True, help="Path to DAV-style forecast JSON list")
    parser.add_argument("--tours-json", required=True, help="Path to Komoot-style tours JSON list")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    weather_client = DAVWeatherClient(_load_json(args.weather_json))
    tours_client = KomootToursClient(_load_json(args.tours_json))

    recommendations = recommend_tours(
        forecasts=weather_client.get_forecasts(),
        tours=tours_client.get_tours(),
        sport=args.sport,
        group_fitness=args.fitness,
    )

    if not recommendations:
        print("No robust-weather tours found for this sport/fitness combination.")
        return 0

    for tour in recommendations:
        print(f"{tour.name} | {tour.area} | {tour.sport} | {tour.fitness_level} | {tour.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
