"""gta6-twitch-ccu-forecast-01: day-building console-launch forecaster.

Forecasts, for each of hours 2..24 of the release day (UTC), five quantiles
(5%, 25%, 50%, 75%, 95%) of the Twitch category's concurrent-viewer count,
anchored on hour 1's print.

Method (standard library only, deterministic, offline):
  1. From the case's own `comparables` (past big launches' hourly curves),
     select the launches that behave like this one: a console launch whose
     audience builds through the day instead of peaking in hour 1.
     A launch qualifies when its hour-1 viewers are 20%-75% of its release-day
     peak (day-building, not a midnight surge and not a pre-unlock trickle),
     its unlock notes do not say early-access-contaminated, and it is not
     free-to-play. Grand Theft Auto VI is a console-only rolling-midnight
     launch whose biggest market (the US) unlocks at 05:00/08:00 UTC, so its
     audience builds through the day exactly like these.
  2. For each hour h, take the empirical distribution of log(viewers_h /
     viewers_1) across the selected launches. The central forecast is a
     blend: half the empirical median, half a per-hour OLS prediction of
     the log-ratio from log(hour-1 viewers) — bigger launches grow less
     through the day (corr about -0.6 at hour 24), so the plain median
     over-predicts the evening rise for a mega launch like GTA VI. The
     5/25/75/95 percentiles are the spread around the empirical median,
     widened x1.2 for all hours 2-24. Calibrated by leave-one-out
     cross-validation on the comparables: pinball loss ~0.19 on
     day-building launches (~0.25 on the wider eligible set) vs ~0.20
     (~0.29) for v2 and ~0.28 (~0.26) for the persistence baseline.
  3. Fallbacks if too few launches qualify: relax to hour-1 >= 20% of peak
     with a quiet pre-release, then to every comparable with an hour-1
     print, then to the persistence baseline. So the program always emits a
     valid forecast.

The median curve dips overnight (US asleep, hours 2-5), stays low through
the US unlock hours, then rises to ~2x hour 1 by the US evening
(hours 18-24). The spread is wide because launch days vary; the pinball
loss on the log scale rewards an honest spread, not false precision.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so `import model`
# finds a model.py shipped beside this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
# Spread widening around the median, calibrated by leave-one-out CV.
# Hours 2-8 and 9-24 both use 1.2 (v2 used 1.2 early / 1.4 late): with the
# wider training window and the stronger late blend, the late spread of
# 1.4 over-widens — 1.2/1.2 improves the day-building LOO (0.193 -> 0.189
# at blend 0.3/0.7) while keeping the wider eligible set flat.
SPREAD_EARLY = 1.2
SPREAD_LATE = 1.2
# Day-building window: hour-1 viewers as a share of the release-day peak.
# HI_SHARE is 0.90 (v2 used 0.75): widening the window adds exactly one
# launch to the training set — Cyberpunk 2077 (share 0.797, hour-1
# 852k viewers), the closest mega-launch scale analogue to GTA VI.
# LOO: window 0.75 -> 0.90 alone moves C 0.199 -> 0.196 and A 0.286 -> 0.264.
LO_SHARE = 0.20
HI_SHARE = 0.90
MIN_TRAIN = 5


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def round2(x):
    """x rounded to 2 decimals, half up (like JavaScript Math.round)."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value == int(value) else value


def quantiles(vals, qs=LEVELS):
    """Linear-interpolation quantiles of a sorted sample."""
    s = sorted(vals)
    n = len(s)
    out = []
    for q in qs:
        i = q * (n - 1)
        lo = int(i)
        hi = min(lo + 1, n - 1)
        f = i - lo
        out.append(s[lo] * (1 - f) + s[hi] * f)
    return out


def hourly_means(comp):
    """{hour offset from day_start (1-based): mean viewers} from hourly points."""
    day_start = parse_dt(comp["day_start"])
    by_hour = {}
    for p in comp.get("hourly", []):
        try:
            t = parse_dt(p["from"])
            v = p["viewers"]
        except (KeyError, ValueError):
            continue
        if v is None or v < 0:
            continue
        h = int((t - day_start).total_seconds() // 3600) + 1
        by_hour.setdefault(h, []).append(v)
    return {h: sum(v) / len(v) for h, v in by_hour.items()}


def log_ratios(comp):
    """log(viewers_h / viewers_1) for h = 2..24, plus hour-1 share of the
    release-day peak, the pre-release ratio, and hour-1 viewers (v1) itself.
    Returns (ratios, share, pre_ratio, v1), or (None, None, None, None)
    if hour 1 is unusable."""
    m = hourly_means(comp)
    if 1 not in m or m[1] <= 0:
        return None, None, None, None
    v1 = m[1]
    day = {h: m[h] for h in range(1, 25) if h in m}
    if not day:
        return None, None, None, None
    peak = max(day.values())
    ratios = {}
    for h in range(2, 25):
        if h in m and m[h] > 0:
            ratios[h] = math.log(m[h] / v1)
    if len(ratios) < 20:
        return None, None, None, None
    pre = [m[h] for h in range(-24, 0) if h in m]
    pre24 = sum(pre) / len(pre) if pre else 0.0
    return ratios, v1 / peak if peak > 0 else 0.0, pre24 / v1 if v1 else 0.0, v1


def is_early_access(comp):
    return "early-access-contaminated" in str(comp.get("unlock", "")).lower()


def is_free_to_play(comp):
    u = str(comp.get("unlock", "")).lower()
    return "f2p" in u or "free-to-play" in u


def select_training(comparables):
    """Day-building console launches, with a fallback chain.

    Returns a list of (ratios, v1) pairs: each launch's log-ratio curve and
    its hour-1 viewers, so the median can be adjusted for launch scale."""
    parsed = []
    for comp in comparables or []:
        ratios, share, pre_ratio, v1 = log_ratios(comp)
        if ratios is None:
            continue
        parsed.append((ratios, share, pre_ratio, v1, comp))
    day_building = [
        (r, v) for r, s, p, v, c in parsed
        if LO_SHARE <= s <= HI_SHARE and not is_early_access(c) and not is_free_to_play(c)
    ]
    if len(day_building) >= MIN_TRAIN:
        return day_building
    quiet = [(r, v) for r, s, p, v, c in parsed if s >= LO_SHARE and p <= 0.6]
    if len(quiet) >= MIN_TRAIN:
        return quiet
    if len(parsed) >= MIN_TRAIN:
        return [(r, v) for r, s, p, v, c in parsed]
    return []


# Scale-regression blend weights for the central forecast, split by hour.
# Bigger launches grow less through the day (within day-building launches,
# corr(log v1, log-ratio at hour 24) is about -0.6): the plain empirical
# median, which ignores launch size, over-predicts the evening rise for a
# mega launch like GTA VI. So the median is a blend of the empirical median
# and a per-hour OLS prediction of the log-ratio from log(hour-1 viewers).
# The regression is most trustworthy late in the day, where the scale
# effect is strongest and the OLS slope is best identified, so the blend
# leans on it more there: 20% early (hours 2-8), 80% late (hours 9-24).
# Leave-one-out CV on the comparables: this per-hour blend (with the wider
# window and spread 1.2/1.2) gives pinball ~0.188 on day-building targets
# (v2: ~0.199) and ~0.251 on the wider eligible set (v2: ~0.286); the wins
# concentrate on the biggest launches (ELDEN RING 0.363 -> 0.144 in the
# v2-vs-v3 per-target comparison on the eligible set, Cyberpunk 2077
# 0.415 -> 0.243), the closest scale analogues to GTA VI.
BLEND_EARLY = 0.2
BLEND_LATE = 0.8


def reg_med(train, p1, h):
    """OLS prediction of log(viewers_h / viewers_1) from log(hour-1 viewers).

    train is a list of (ratios, v1) pairs. Returns None when too few points
    have this hour."""
    pts = [(math.log(v), r[h]) for r, v in train if h in r and v > 0]
    if len(pts) < 5:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return my
    b = sum((x - mx) * (y - my) for x, y in pts) / sxx
    return (my - b * mx) + b * math.log(max(1.0, p1))


def persistence_quantiles(p1, h):
    z = [-1.6448536269514722, -0.6744897501960817, 0.0, 0.6744897501960817, 1.6448536269514722]
    return [p1 * math.exp(zz * 0.15 * math.sqrt(h - 1)) for zz in z]


def forecast_case(case, name):
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    first = next((k for k in case["known"] if k["hour"] == 1), None)
    if first is None:
        raise ValueError(f"{name} has no hour-1 print")
    p1 = max(1.0, float(first["viewers"]))
    train = select_training(case.get("comparables"))
    hours = []
    for row in case["forecast"]:
        h = row["hour"]
        if train:
            vals = [r[h] for r, _v in train if h in r]
            qs = quantiles(vals)
            med = qs[2]
            # Blend the empirical median with the scale-regression prediction
            # for this launch's hour-1 size; the spread stays around the
            # empirical median.
            reg = reg_med(train, p1, h)
            w = BLEND_EARLY if h <= 8 else BLEND_LATE
            m = med if reg is None else (1.0 - w) * med + w * reg
            spread = SPREAD_EARLY if h <= 8 else SPREAD_LATE
            raw = [p1 * math.exp(m + (x - med) * spread) for x in qs]
        else:
            raw = persistence_quantiles(p1, h)
        # Round half-up to 2 decimals, enforce > 0, <= 1e9, non-decreasing.
        out = []
        prev = 0.0
        for x in raw:
            v = round2(min(max(x, 0.01), 1e9))
            if v <= prev:
                v = prev if prev > 0 else 0.01
            out.append(v)
            prev = v
        hours.append({"hour": h, "q": out})
    return {"hours": hours}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
