import unittest
import json
import tempfile
from pathlib import Path

from alpine_planner import (
    DAVWeatherClient,
    KomootToursClient,
    Tour,
    WeatherForecast,
    _load_json,
    can_group_do_tour,
    has_robust_good_weather,
    recommend_tours,
)


class PlannerTests(unittest.TestCase):
    def test_robust_good_weather_accepts_safe_conditions(self):
        forecast = WeatherForecast(
            area="Chamonix",
            condition="sunny",
            precipitation_mm=0.2,
            wind_kmh=18,
            visibility_km=20,
        )
        self.assertTrue(has_robust_good_weather(forecast))

    def test_robust_good_weather_rejects_windy_conditions(self):
        forecast = WeatherForecast(
            area="Zermatt",
            condition="sunny",
            precipitation_mm=0.1,
            wind_kmh=42,
            visibility_km=15,
        )
        self.assertFalse(has_robust_good_weather(forecast))

    def test_group_fitness_must_meet_tour_fitness(self):
        self.assertTrue(can_group_do_tour("hard", "moderate"))
        self.assertFalse(can_group_do_tour("easy", "hard"))

    def test_recommend_tours_filters_by_weather_sport_and_fitness(self):
        forecasts = [
            WeatherForecast("Chamonix", "sunny", 0, 10, 15),
            WeatherForecast("Davos", "rain", 4, 15, 5),
        ]
        tours = [
            Tour("Balcon Nord", "Chamonix", "hiking", "easy", "komoot"),
            Tour("Haute Route", "Chamonix", "mountaineering", "hard", "komoot"),
            Tour("Parsenn", "Davos", "skiing", "moderate", "komoot"),
        ]

        results = recommend_tours(forecasts, tours, sport="hiking", group_fitness="moderate")

        self.assertEqual([t.name for t in results], ["Balcon Nord"])

    def test_recommend_tours_orders_by_fitness_then_name(self):
        forecasts = [WeatherForecast("Chamonix", "sunny", 0, 10, 15)]
        tours = [
            Tour("Zulu Route", "Chamonix", "hiking", "moderate", "komoot"),
            Tour("Alpha Traverse", "Chamonix", "hiking", "moderate", "komoot"),
            Tour("Beginner Loop", "Chamonix", "hiking", "easy", "komoot"),
        ]

        results = recommend_tours(forecasts, tours, sport="hiking", group_fitness="hard")

        self.assertEqual(
            [t.name for t in results],
            ["Beginner Loop", "Alpha Traverse", "Zulu Route"],
        )

    def test_recommend_tours_matches_case_insensitive_area_and_sport(self):
        forecasts = [WeatherForecast("Chamonix", "sunny", 0, 10, 15)]
        tours = [Tour("Balcon Nord", "chamonix", "Hiking", "easy", "komoot")]

        results = recommend_tours(forecasts, tours, sport="hiking", group_fitness="moderate")

        self.assertEqual([t.name for t in results], ["Balcon Nord"])

    def test_json_loading_flow_for_provider_clients(self):
        weather_data = [
            {
                "area": "Chamonix",
                "condition": "sunny",
                "precipitation_mm": 0.2,
                "wind_kmh": 12,
                "visibility_km": 18,
            }
        ]
        tours_data = [
            {
                "name": "Balcon Nord",
                "area": "Chamonix",
                "sport": "hiking",
                "fitness_level": "easy",
                "source": "komoot",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            weather_path = Path(tmp) / "weather.json"
            tours_path = Path(tmp) / "tours.json"
            weather_path.write_text(json.dumps(weather_data), encoding="utf-8")
            tours_path.write_text(json.dumps(tours_data), encoding="utf-8")

            weather_client = DAVWeatherClient(_load_json(str(weather_path)))
            tours_client = KomootToursClient(_load_json(str(tours_path)))

            self.assertEqual(weather_client.get_forecasts()[0].area, "Chamonix")
            self.assertEqual(tours_client.get_tours()[0].name, "Balcon Nord")


if __name__ == "__main__":
    unittest.main()
