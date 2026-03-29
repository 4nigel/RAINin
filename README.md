# RainIn

**NZ construction weather disruption risk estimator**

RainIn estimates the probability of weather-related disruption, week by week, across a construction project programme. It is built for New Zealand residential and social housing projects and uses real NIWA climate data.

---

## What it does

Given a project address and start/end dates, RainIn:

- Geocodes the address to find the nearest NIWA weather station
- Maps each project week to the corresponding historical climate data
- Applies configurable disruption thresholds (rain, wind, minimum temperature)
- Returns a weekly disruption probability and dominant driver (rain / wind / temp)
- Displays results as a colour-coded bar chart and a scrollable weekly table
- Exports the report as PDF, SVG, or PNG

---

## How to use it

RainIn is a single HTML file. No installation, no server, no dependencies to manage.

1. Download `rainin.html`
2. Open it in any modern browser (Chrome, Firefox, Edge, Safari)
3. Enter a NZ address or suburb, project dates, and trade type
4. Click **Run analysis**

An internet connection is required only for the geocoding step (address → coordinates). All climate data is embedded in the file.

---

## Files in this repository

| File | Description |
|---|---|
| `rainin.html` | The complete application — open this in a browser |
| `rainin_data.json` | Pre-processed climate data, embedded in rainin.html |
| `rainin_preprocess.py` | Script to regenerate rainin_data.json from NIWA EPW/STAT files |
| `LICENSE` | MIT licence |

---

## Climate data

Climate data is sourced from **NIWA TMY3 (Typical Meteorological Year)** files, constructed from 2005–2023 station records. 18 stations across New Zealand are included:

| Code | Location | Code | Location |
|---|---|---|---|
| AK | Auckland | NM | Nelson |
| BP | Tauranga | NP | New Plymouth |
| CC | Christchurch | OC | Lauder (Central Otago) |
| DN | Dunedin | QL | Queenstown |
| EC | Napier | RR | Rotorua |
| HN | Hamilton | TP | Turangi |
| IN | Invercargill | WC | Hokitika |
| MW | Paraparaumu | WI | Masterton |
| NL | Kaitaia | WN | Wellington |

Each project address is matched to the nearest station by Haversine distance. A distance badge (green / amber / red) indicates data confidence.

The NIWA TMY3 files are not redistributed in this repository. If you need to regenerate `rainin_data.json` from updated NIWA source files, use `rainin_preprocess.py`.

---

## Disruption thresholds

A day is flagged as disrupted when **any** threshold is exceeded. Defaults by trade:

| Trade | Rain | Wind | Min temp |
|---|---|---|---|
| General site work | > 2 mm | > 35 kph | < 5 °C |
| Roofing | > 1 mm | > 25 kph | < 5 °C |
| Concrete / foundations | > 2 mm | > 40 kph | < 5 °C |
| Timber framing | > 2 mm | > 35 kph | < 3 °C |
| Cladding / exterior | > 1 mm | > 30 kph | < 5 °C |
| Painting / coatings | > 0.5 mm | > 20 kph | < 10 °C |
| Earthworks | > 5 mm | > 50 kph | < 0 °C |

All thresholds are adjustable via sliders in the app.

Weekly probability is calculated as the proportion of working days in that week where at least one threshold is exceeded, based on TMY3 typical-year data.

---

## Geocoding

Address search uses the [Nominatim](https://nominatim.openstreetmap.org/) API, powered by OpenStreetMap data.

- No API key required
- Suburb names, street addresses, and town names all work
- Data attribution: © OpenStreetMap contributors, ODbL 1.0

---

## Regenerating the data file

If NIWA publishes updated TMY3 files, you can regenerate `rainin_data.json` using the pre-processor:

```bash
python rainin_preprocess.py --epw ./epw_files --stat ./stat_files --out rainin_data.json
```

Then replace the embedded data block in `rainin.html` — it is clearly marked with a comment near the bottom of the file.

Requirements: Python 3.8+, no external libraries.

---

## FOSS commitments

RainIn is free and open-source software. Specifically:

- **Free to use** — no cost, no account, no licence key
- **Free to modify** — change thresholds, add trade types, adapt the UI, extend the algorithm
- **Free to redistribute** — share the HTML file as-is or modified; the only requirement is that you retain the licence notice and data attributions
- **No telemetry** — the app makes no outbound requests except the single Nominatim geocoding call when you run an analysis. No usage data is collected or transmitted
- **No server required** — runs entirely in the browser. The file can be saved locally and used offline (after the first geocoding run)
- **Transparent data** — the embedded climate data is human-readable JSON; the pre-processor script that generated it is included

Licence: **MIT** — see `LICENSE`.

---

## Limitations and caveats

- Results are based on **typical-year** climate statistics, not forecasts. Actual weather will vary.
- The 18 NIWA stations cover NZ's main urban centres well. Projects in rural or remote locations may be assigned to a station 75–150 km away; the distance badge flags this.
- Wellington's disruption probability (typically 85–90%) is correct — wind is the dominant driver there year-round. This is not a bug.
- Humidity is not used as a standalone disruption trigger in this version. Canterbury and most NZ locations have high ambient humidity at night and early morning that would flag almost every day. Humidity is retained in the data for future trade-specific profiles (e.g. membrane waterproofing).

---

## Roadmap

Possible future additions — contributions welcome:

- Humidity threshold for membrane / waterproofing trade
- TAKT planning integration (weekly risk overlay on TAKT wave diagram)
- NZ map SVG with station markers
- Scenario comparison (present climate vs future-climate TMY3 files)
- Real-time forecast adjustment for near-term weeks

---

## Credits

- Climate data: [NIWA](https://niwa.co.nz/) TMY3 files, 2005–2023
- Geocoding: [Nominatim](https://nominatim.openstreetmap.org/) / © OpenStreetMap contributors
- Chart rendering: [Chart.js](https://www.chartjs.org/) (MIT)
- PNG export: [html2canvas](https://html2canvas.hertzen.com/) (MIT)
- Concept, design, and development: Nigel Lamb / [Empiricus Design](https://github.com/4nigel)
