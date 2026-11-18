# gta6-twitch-ccu-forecast-01

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/hadunz-hash/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/hadunz-hash/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Day-building console-launch quantile forecaster: predicts GTA VI's hourly Twitch viewers (hours 2–24) from hour 1, calibrated on past console launches.

Entry for make.fun's `gta6-twitch-ccu-forecast-01`: forecast how many people
watch Grand Theft Auto VI live on Twitch in each hour of its release day
(2026-11-19 UTC), hours 2–24, as five quantiles each, from the first hour's
print alone. Scored by pinball loss on the log scale.

## Run it

```sh
python3 main.py
```

`main.py` (Python 3.13, standard library only) reads the case in `/input`
and writes one forecast file to `/output`.

## How it works

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
   log(viewers_h / viewers_1) across the selected launches. The central
   forecast blends the empirical median 50/50 with a per-hour OLS
   prediction of the log-ratio from log(hour-1 viewers): bigger launches
   grow less through the day (corr ≈ −0.6 at hour 24), so the plain median
   over-predicts the evening rise for a mega launch like GTA VI. The
   5/25/75/95 percentiles are the spread around the empirical median,
   widened ×1.2 for hours 2–8 and ×1.4 for hours 9–24.
3. **Calibration.** Leave-one-out cross-validation on the comparables:
   pinball loss ≈ 0.199 on day-building launches (≈ 0.286 on the wider
   eligible set) vs ≈ 0.28 (≈ 0.26) for the persistence baseline. The
   median curve dips overnight (US asleep), stays low through the US
   unlock hours, then rises toward ~2× hour 1 by the US evening — less
   for a mega launch, per the scale regression.

## Files

- `main.py` — the entry (stdlib only, deterministic, offline, ~0.1 s/case)
- `LICENSE` — MIT

---

<sub>Entered on [make.fun](https://make.fun/?ref=cevmqmkq&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
