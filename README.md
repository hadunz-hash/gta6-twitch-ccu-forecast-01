# GTA VI Twitch viewers — hour-by-hour forecast

Entry for make.fun's `gta6-twitch-ccu-forecast-01`: forecast how many people
watch Grand Theft Auto VI live on Twitch in each hour of its release day
(2026-11-19 UTC), hours 2–24, as five quantiles each, from the first hour's
print alone. Scored by pinball loss on the log scale.

## How it works

`main.py` (Python 3.13, standard library only) reads the case in `/input`
and writes one forecast file to `/output`.

1. **Training set, chosen at run time from the case's own comparables.**
   A past launch qualifies when its hour-1 viewers are 20%–75% of its
   release-day peak (a day-building launch, not a midnight surge and not a
   pre-unlock trickle), its unlock notes do not say early-access-contaminated,
   and it is not free-to-play. GTA VI is a console-only rolling-midnight
   launch whose biggest market (the US) unlocks at 05:00/08:00 UTC, so its
   audience builds through the day exactly like these launches. (Fallbacks:
   hour-1 ≥ 20% of peak with a quiet pre-release, then every comparable
   with an hour-1 print, then the persistence baseline — so the program
   always emits a valid forecast.)
2. **Quantiles.** For each hour, the empirical distribution of
   log(viewers_h / viewers_1) across the selected launches: the median is
   the central forecast, the 5/25/75/95 percentiles the spread, widened
   ×1.2 around the median.
3. **Calibration.** Leave-one-out cross-validation on the comparables:
   pinball loss ≈ 0.20 on day-building launches vs ≈ 0.28 for the
   persistence baseline on the same launches. The median curve dips
   overnight (US asleep), stays low through the US unlock hours, then rises
   to ~2× hour 1 by the US evening.

## Files

- `main.py` — the entry (stdlib only, deterministic, offline, ~0.1 s/case)
- `LICENSE` — MIT
