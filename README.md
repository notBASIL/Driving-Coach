# Driving Coach

A personal, phone-based driving coach. It scores each trip on the six factors TD MyAdvantage
describes (acceleration, braking, cornering, distractions, duration, speed), with live voice
alerts while you drive. Scores are coaching estimates, not TD's numbers. Posted signs always
take priority.

**Open the app:** https://notbasil.github.io/Driving-Coach/
(then Share → Add to Home Screen in Safari)

See [CHANGELOG.md](CHANGELOG.md) for the patch notes.

## How it's built
| Part | What it does |
|---|---|
| `driving-coach.html` | The whole app (one file). Trips and settings stay on the phone. |
| `index.html` | Short link that opens the app. |
| `icon.svg`, `apple-touch-icon.png` | Browser-tab and home-screen icons. |
| `roads/` | London-area road map with speed limits, split into small pieces the app loads near you. Generated, don't edit by hand. |
| `roads/roadwork.json` | City of London ongoing road work. Generated daily. |
| `tools/build_roads.py`, `tools/official.py` | Build `roads/` from OpenStreetMap plus official speed limits. |
| `tools/build_roadwork.py` | Builds `roads/roadwork.json`. |
| `tools/area.json` | The area covered by the map. |
| `.github/workflows/` | Monthly map rebuild and daily road-work update. |
| `CHANGELOG.md` | Patch notes; every push is recorded here. |
| `CLAUDE.md` | Working rules for Claude on this repo. |

## Data sources and credits
- Speed limits and road work: City of London Open Data.
- Ontario Road Network, Ontario Ministry of Natural Resources, under the Open Government Licence – Ontario.
- Map data © OpenStreetMap contributors (ODbL), via Geofabrik.
- Title font: Pacifico (Google Fonts, SIL Open Font License).
