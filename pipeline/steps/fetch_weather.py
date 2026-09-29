"""Weather forecast (morning / day / evening) for every trip day and location, from Open-Meteo.

Source: Open-Meteo forecast API (https://api.open-meteo.com/v1/forecast, no key; data CC BY 4.0).
Hourly temperature_2m, precipitation_probability, precipitation, cloud_cover, weather_code in local time
(America/Bogota), 16 forecast days, with `elevation` passed so the temperature is corrected to the
site's altitude (grid cells in the Andes are coarse).

Locations per day of data/itinerary.json: `sites[]` plus `overnight_site` (deduped, overnight last and
merged into a day site of the same id). Coordinates and elevation from data/sites_resolved.json
(elevation = mean of elev_min/elev_max, else the day's `elev_sleep` for the overnight site). Days with no
overnight site use a Bogotá fallback (FALLBACK) as the overnight location. One request per distinct
location; only days inside the forecast window get an entry.

Periods (local time, hour starts): morning 06-09 (06:00-10:00), day 10-15 (10:00-16:00),
evening 16-18 (16:00-19:00). Per period: t_min/t_max (°C, int), precip_prob (max %), precip (sum mm,
1 decimal), cloud_cover (mean %), weather_code = the most severe WMO code of the period's hours (WMO codes
grow with severity: clear 0 < clouds 1-3 < fog 45/48 < drizzle 51-57 < rain 61-67 < snow 71-77 <
showers 80-86 < thunderstorm 95-99), so one rainy hour shows as rain: for a field trip the worst hour
matters more than the typical one.

Output: data/weather.json (see site/src/lib/data.ts `Weather`). Forecasts must be fresh, so this step
does not use the pipeline HTTP cache. When no trip day falls inside the forecast window the file is left
untouched (cron runs after the trip commit nothing).
"""
from __future__ import annotations

import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, USER_AGENT, log, read_json, status, write_json  # noqa: E402

API = "https://api.open-meteo.com/v1/forecast"
TZ = "America/Bogota"
FORECAST_DAYS = 16
HOURLY = "temperature_2m,precipitation_probability,precipitation,cloud_cover,weather_code"
PERIODS = {"morning": (6, 10), "day": (10, 16), "evening": (16, 19)}  # [start, end) local hours
FALLBACK = {"id": "bogota", "name_ru": "Богота", "lat": 4.61, "lon": -74.08, "elevation": 2600}
OUT = DATA / "weather.json"


def fetch(lat: float, lon: float, elevation: float | None) -> dict:
    params: dict = {"latitude": lat, "longitude": lon, "hourly": HOURLY, "timezone": TZ,
                    "forecast_days": FORECAST_DAYS}
    if elevation is not None:
        params["elevation"] = elevation
    delay = 2.0
    for attempt in range(5):
        try:
            r = httpx.get(API, params=params, timeout=60, headers={"User-Agent": USER_AGENT})
            if r.status_code == 200:
                return r.json()
            err = f"HTTP {r.status_code}: {r.text[:200]}"
            if r.status_code < 500 and r.status_code != 429:
                raise RuntimeError(err)
        except httpx.HTTPError as e:
            err = f"{type(e).__name__}: {e}"
        log(f"  open-meteo attempt {attempt + 1} failed ({err}), retrying in {delay:.0f}s")
        time.sleep(delay)
        delay *= 2
    raise RuntimeError(f"open-meteo unreachable for {lat},{lon}: {err}")


def aggregate(hourly: dict) -> dict[str, dict[str, dict]]:
    """{date: {period: stats}} from Open-Meteo's hourly arrays (local-time ISO strings)."""
    by_day: dict[str, dict[str, list[int]]] = {}
    for i, t in enumerate(hourly["time"]):
        d, hh = t[:10], int(t[11:13])
        for name, (a, b) in PERIODS.items():
            if a <= hh < b:
                by_day.setdefault(d, {}).setdefault(name, []).append(i)
    out: dict[str, dict[str, dict]] = {}
    for d, periods in by_day.items():
        for name, idx in periods.items():
            def vals(key: str) -> list:
                return [hourly[key][i] for i in idx if hourly[key][i] is not None]
            temp, prob, prec = vals("temperature_2m"), vals("precipitation_probability"), vals("precipitation")
            cloud, code = vals("cloud_cover"), vals("weather_code")
            if not temp:
                continue
            out.setdefault(d, {})[name] = {
                "t_min": round(min(temp)),
                "t_max": round(max(temp)),
                "precip_prob": round(max(prob)) if prob else None,
                "precip": round(sum(prec), 1) if prec else None,
                "cloud_cover": round(sum(cloud) / len(cloud)) if cloud else None,
                "weather_code": int(max(code)) if code else None,
            }
    return out


def elev_of(site: dict) -> float | None:
    lo, hi = site.get("elev_min"), site.get("elev_max")
    if lo is not None and hi is not None:
        return round((lo + hi) / 2)
    return lo if lo is not None else hi


def main() -> None:
    itinerary = read_json(DATA / "itinerary.json")
    sites = {s["id"]: s for s in read_json(DATA / "sites_resolved.json")}
    today = datetime.now(ZoneInfo(TZ)).date()
    last = today + timedelta(days=FORECAST_DAYS - 1)
    days = [d for d in itinerary if today <= date.fromisoformat(d["date"]) <= last]
    if not days:
        log(f"weather: no trip day within {today}..{last}, data/weather.json left untouched")
        return

    # per day: [(location, overnight)], location = {id, name_ru, lat, lon, elevation}
    plan: dict[str, list[tuple[dict, bool]]] = {}
    locations: dict[str, dict] = {}
    for d in days:
        entries: list[tuple[dict, bool]] = []
        for sid in d.get("sites") or []:
            s = sites[sid]
            loc = locations.setdefault(sid, {"id": sid, "name_ru": s.get("name_ru") or s["name"],
                                             "lat": s["lat"], "lon": s["lon"], "elevation": elev_of(s)})
            if all(e[0]["id"] != sid for e in entries):
                entries.append((loc, False))
        oid = d.get("overnight_site")
        if oid:
            s = sites[oid]
            loc = locations.setdefault(oid, {"id": oid, "name_ru": s.get("name_ru") or s["name"],
                                             "lat": s["lat"], "lon": s["lon"],
                                             "elevation": elev_of(s) or d.get("elev_sleep")})
        else:
            loc = locations.setdefault("bogota", dict(FALLBACK))
        entries = [e for e in entries if e[0]["id"] != loc["id"]] + [(loc, True)]
        plan[d["date"]] = entries

    forecasts: dict[str, dict] = {}
    failed: list[str] = []
    for n, (lid, loc) in enumerate(locations.items(), 1):
        status("weather", n - 1, len(locations), f"weather: {lid} ({loc['lat']}, {loc['lon']}, {loc['elevation']} m)")
        try:
            forecasts[lid] = aggregate(fetch(loc["lat"], loc["lon"], loc["elevation"])["hourly"])
        except RuntimeError as e:  # one flaky location must not drop the whole forecast
            log(f"  WARNING: {e}")
            failed.append(lid)
            forecasts[lid] = {}
    if len(failed) == len(locations):
        sys.exit(f"weather: every request failed, {OUT.name} left untouched")

    out_days: dict[str, dict] = {}
    for d, entries in plan.items():
        rows = []
        for loc, overnight in entries:
            periods = forecasts[loc["id"]].get(d)
            if periods:
                rows.append({"id": loc["id"], "name_ru": loc["name_ru"], "elevation": loc["elevation"],
                             "overnight": overnight, "periods": periods})
        if rows:
            out_days[d] = {"sites": rows}
    write_json(OUT, {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "open-meteo",
        "days": out_days,
    })
    status("weather", len(locations), len(locations),
           f"weather: {len(out_days)} days, {len(locations) - len(failed)}/{len(locations)} locations"
           f"{' (failed: ' + ', '.join(failed) + ')' if failed else ''} -> {OUT.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
