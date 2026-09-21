import unittest

from alpine_planner import (
    Tour,
    WeatherForecast,
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


if __name__ == "__main__":
    unittest.main()
