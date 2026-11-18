# Driving Coach – patch notes

A personal driving coach that scores every trip on the same six factors TD MyAdvantage uses
(acceleration, braking, cornering, distractions, duration, speed). Scores are coaching
estimates, not TD's numbers. Posted signs always take priority.

App: https://notbasil.github.io/Driving-Coach/driving-coach.html

---

## v3.3 — Road work, trends and backup
- **Construction warnings.** The City of London's ongoing road work (about 475 sites) is downloaded daily. A banner, a voice alert and a screen flash warn you when road work is up to ~300 m ahead on your road or you're in it, once per zone per trip. Settings → Road work warnings turns it off.
- **Temporary speed limits.** The limit picker has a "Temporary (road work)" option, pre-ticked inside road work. The sign shows **TEMP**, and the limit returns to normal by itself after 14 days.
- **Weekly trends** on Stats: weekly score chart with 3★/4★/5★ guides (tap a week for details) and a trend line per factor with ▲/▼ versus the previous week.
- **Backup to Files** through the iPhone share sheet, **Restore from a backup file** (no duplicates, includes speed-limit fixes), and a weekly backup reminder once you have 3+ trips.
- Drive screen redraws only when something visible changes (less work while driving).
- Behind the scenes: the monthly map rebuild and the daily road-work update take turns, and the map rebuild no longer touches road-work data. `notbasil.github.io/Driving-Coach/` now opens the app directly.
- Every update is now recorded in these patch notes (rule saved in the repo's `CLAUDE.md`).

## v3.2 — Tab bar icons
- New line icons for Drive (steering wheel), Trips (route), Stats (bars and a star) and Settings (sliders), with a highlighted pill on the active tab. Themed in every design.

## v3.1 — Cleaner header
- Sound button is icon-only (speaker, or amber speaker with ✕ when muted).
- Clock removed from the top bar.
- "Driving Coach" title in the **Pacifico** script font.

## v3 — Themes
- Theme picker (palette button, or Settings → Look) with six full designs, each with its own Drive screen and Trip card:
  **Classic**, **Midnight Road** (speed dial), **Daylight** (big number, sign and bar),
  **Night HUD** (dashboard readout and segment bar), **Glance** (whole screen turns green, amber or red),
  **Road View** (your drive drawn as a road), plus **Auto** (Daylight 7 AM–7 PM, Midnight Road after).

## v2.3 — Official speed limits
- London-area speed limits now come from official sources, merged onto the map:
  City of London by-law limits (including the 40 km/h zones), the Ontario default of 50 for unlisted city streets,
  and the Ontario Road Network for highways and rural roads, with OpenStreetMap as backup.
  About 96% of road length now has a known limit (up from about 41%).
- The sign shows where each limit came from: CITY, LAW, ONT., POSTED or GUESS.
- Map data is built from Geofabrik's daily Ontario extract instead of the busy public map server.
- Data credits added to Settings.

## v2.2 — Self-update
- The app checks for a newer version on open and shows a one-tap "New version available" button.

## v2.1 — Move your data
- Settings → Copy my data / Import data moves trips (and speed-limit fixes) between the browser and the home-screen app. Importing twice doesn't create duplicates.

## v2 — New icon
- New **Road to Five** app icon for the home screen and browser tab.

## v1.5 — Map hosted on the site
- London's road and speed-limit map is stored on the app's own site (refreshed monthly by a GitHub Action), so limits load in about a second without depending on a public server. The live server is used only outside London.

## v1.4 — Version label
- Version number shown next to the title, so you can tell which version you're running.

## v1.3 — Road name and steadier limits
- Current road shown in large text; the limit updates automatically as you change roads.
- Untagged pieces of a street borrow the posted limit of the same street nearby.
- Road switching is steadier (no flicker near side streets).
- Spoken "Speed limit 60" when the limit changes.
- One-tap mute button, plus separate beep/voice switches.
- Map loading no longer gets stuck: request timeouts, backup servers, smaller areas, cached areas for offline use.

## v1.2 — Speed-limit matching
- Speed limits are matched to the road you're actually on (position and direction of travel), ignoring cross streets.
- Correct a wrong limit by tapping the sign while stopped; corrections are saved per road.
- Trip card lists the roads and limits used, each with a Fix button.
- Map status pill.

## v1.1 — First version
- Web app that scores each trip 1–5 stars on acceleration, braking, cornering, distractions, duration and speed.
- GPS and motion sensors, live beeps and voice alerts, night driving (11 PM–5 AM) weighted 1.5×.
- Trips are detected automatically and end after 5 minutes parked.
- Trips list, trip details with events and map links, stats, settings (Strict/Normal), demo trip, CSV/JSON export.
