# follow_the_sun

Alpine weather + tour planning helper.

This lightweight CLI helps identify **Alps areas with robustly good weather** for:
- hiking
- skiing
- mountaineering

Then it filters tours (e.g. Komoot-like input) by:
- weather-safe areas
- selected sport
- your group's fitness level (easy/moderate/hard)

## Run

```bash
python alpine_planner.py \
  --sport hiking \
  --fitness moderate \
  --weather-json /absolute/path/weather.json \
  --tours-json /absolute/path/tours.json
```

## Input format

`weather.json` (DAV-style list):
```json
[
  {
    "area": "Chamonix",
    "condition": "sunny",
    "precipitation_mm": 0.2,
    "wind_kmh": 12,
    "visibility_km": 18
  }
]
```

`tours.json` (Komoot-style list):
```json
[
  {
    "name": "Balcon Nord",
    "area": "Chamonix",
    "sport": "hiking",
    "fitness_level": "easy",
    "source": "komoot"
  }
]
```

## Value constraints

- `condition` should represent stable weather (recommended values: `sunny`, `partly_cloudy`)
- `sport` must be one of: `hiking`, `skiing`, `mountaineering`
- `fitness` (CLI) and `fitness_level` (tour entries) should be one of: `easy`, `moderate`, `hard`
