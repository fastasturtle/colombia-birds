"""Build the static SVG base map for the route page from Natural Earth (public domain).

Downloads Natural Earth 10m GeoJSON layers (cached in pipeline/cache/naturalearth/), clips them to a
bbox around data/sites.json (+- MARGIN degrees), simplifies, projects with an equirectangular
projection (x scaled by cos(mid latitude)) into an SVG viewBox 0 0 1000 H and writes
site/src/generated/basemap.json (checked in, so the site builds without running the pipeline).

Run: cd pipeline && uv run --with shapely python run.py basemap
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import httpx
from shapely.geometry import Point, box, shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import CACHE, DATA, ROOT, atomic_write, log  # noqa: E402

NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
NE_DIR = CACHE / "naturalearth"
OUT = ROOT / "site" / "src" / "generated" / "basemap.json"
MARGIN = 0.8
TOL = 0.01  # simplify tolerance, degrees
WIDTH = 1000
NEIGHBORS = {"ECU", "PER", "BRA", "VEN", "PAN"}
RIVER_MAX_SCALERANK = 9
# (name, name_ru) -> looked up in ne_10m_populated_places by NAME; coords given here are used when
# Natural Earth has no such place (Pitalito, Puerto Asis are too small for the 10m layer).
PLACES = [
    ("Bogota", "Богота", None), ("Cali", "Кали", None), ("Pasto", "Пасто", None),
    ("Popayán", "Попаян", None), ("Neiva", "Нейва", None), ("Pitalito", "Питалито", (-76.051, 1.853)),
    ("Mocoa", "Мокоа", None), ("Puerto Asís", "Пуэрто-Асис", (-76.496, 0.505)),
    ("Tumaco", "Тумако", None), ("Ipiales", "Ипьялес", None), ("Florencia", "Флоренсия", None),
    ("Quito", "Кито", None),
]
COUNTRY_LABELS = [("ECU", "ЭКВАДОР"), ("PER", "ПЕРУ"), ("COL", "КОЛОМБИЯ")]
RIVER_LABELS = {"Magdalena": "р. Магдалена", "Cauca": "р. Каука", "Caquetá": "р. Какета",
                "Putumayo": "р. Путумайо"}


def ne(name: str) -> list[dict]:
    path = NE_DIR / f"{name}.geojson"
    if not path.exists():
        NE_DIR.mkdir(parents=True, exist_ok=True)
        log(f"download {name}")
        r = httpx.get(NE_BASE + f"{name}.geojson", timeout=300, follow_redirects=True)
        r.raise_for_status()
        atomic_write(path, r.content)
    return json.loads(path.read_text())["features"]


def main() -> None:
    sites = json.loads((DATA / "sites.json").read_text())
    lon0 = min(s["lon"] for s in sites) - MARGIN
    lon1 = max(s["lon"] for s in sites) + MARGIN
    lat0 = min(s["lat"] for s in sites) - MARGIN
    lat1 = max(s["lat"] for s in sites) + MARGIN
    bb = box(lon0, lat0, lon1, lat1)
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    scale = WIDTH / ((lon1 - lon0) * kx)
    height = round((lat1 - lat0) * scale)
    proj = {"lon0": lon0, "lat1": lat1, "kx": kx, "scale": scale}

    def xy(lon: float, lat: float) -> tuple[float, float]:
        return round((lon - lon0) * kx * scale, 1), round((lat1 - lat) * scale, 1)

    def fmt(v: float) -> str:
        return f"{v:.1f}".rstrip("0").rstrip(".")

    def ring(coords, close: bool) -> str:
        pts = [xy(*c[:2]) for c in coords]
        out, prev = [], None
        for p in pts:
            if p != prev:
                out.append(f"{fmt(p[0])} {fmt(p[1])}")
            prev = p
        if len(out) < 2:
            return ""
        return "M" + "L".join(out) + ("Z" if close else "")

    def path(g) -> str:
        if g.is_empty:
            return ""
        t = g.geom_type
        if t == "Polygon":
            return "".join(ring(r.coords, True) for r in [g.exterior, *g.interiors])
        if t == "LineString":
            return ring(g.coords, False)
        if t == "LinearRing":
            return ring(g.coords, True)
        if hasattr(g, "geoms"):
            return "".join(path(p) for p in g.geoms)
        return ""

    def clip(g):
        return g.intersection(bb).simplify(TOL, preserve_topology=True)

    countries = {f["properties"]["ADM0_A3"]: shape(f["geometry"]) for f in ne("ne_10m_admin_0_countries")}
    colombia = countries["COL"]
    neighbors = unary_union([g for k, g in countries.items() if k in NEIGHBORS and g.intersects(bb)])

    depts = [shape(f["geometry"]) for f in ne("ne_10m_admin_1_states_provinces")
             if f["properties"].get("adm0_a3") == "COL" and shape(f["geometry"]).intersects(bb)]
    inner = unary_union([d.boundary for d in depts]).difference(colombia.boundary.buffer(0.02))

    rivers, river_labels = [], []
    for f in ne("ne_10m_rivers_lake_centerlines"):
        p = f["properties"]
        g = shape(f["geometry"])
        if (p.get("scalerank") or 99) <= RIVER_MAX_SCALERANK and g.intersects(bb):
            rivers.append(g)
    river_geom = unary_union(rivers)
    by_name: dict[str, list] = {}
    for f in ne("ne_10m_rivers_lake_centerlines"):
        n = f["properties"].get("name")
        if n in RIVER_LABELS:
            g = shape(f["geometry"]).intersection(bb)
            if not g.is_empty:
                by_name.setdefault(n, []).append(g)
    for n, gs in by_name.items():
        g = unary_union(gs)
        lines = list(g.geoms) if hasattr(g, "geoms") else [g]
        line = max(lines, key=lambda l: l.length)
        a, b = line.interpolate(0.45, normalized=True), line.interpolate(0.55, normalized=True)
        (x0, y0), (x1, y1) = xy(a.x, a.y), xy(b.x, b.y)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        mx, my = xy(*line.interpolate(0.5, normalized=True).coords[0])
        river_labels.append({"name": RIVER_LABELS[n], "x": mx, "y": my, "angle": round(ang)})

    lakes = [shape(f["geometry"]) for f in ne("ne_10m_lakes") if shape(f["geometry"]).intersects(bb)]

    pp = {}
    for f in ne("ne_10m_populated_places"):
        p = f["properties"]
        if p.get("ADM0NAME") in ("Colombia", "Ecuador"):
            pp.setdefault(p["NAME"], (p["LONGITUDE"], p["LATITUDE"]))
    places = []
    for name, name_ru, fallback in PLACES:
        ll = pp.get(name) or fallback
        if not ll or not bb.contains(Point(ll)):
            log(f"place skipped: {name}")
            continue
        x, y = xy(*ll)
        places.append({"name": name, "name_ru": name_ru, "x": x, "y": y, "capital": name == "Bogota"})

    country_labels = []
    for code, label in COUNTRY_LABELS:
        g = countries[code].intersection(bb)
        if g.is_empty:
            continue
        pt = g.representative_point() if code != "COL" else Point(-74.3, 2.2)
        x, y = xy(pt.x, pt.y)
        country_labels.append({"name": label, "x": x, "y": y})

    out = {
        "source": "Natural Earth 1:10m (public domain), naturalearthdata.com",
        "bbox": [round(lon0, 3), round(lat0, 3), round(lon1, 3), round(lat1, 3)],
        "viewBox": [0, 0, WIDTH, height],
        "projection": {k: round(v, 6) for k, v in proj.items()},
        "neighbors": path(clip(neighbors.difference(colombia))),
        "colombia": path(clip(colombia)),
        "departments": path(clip(inner)),
        "rivers": path(clip(river_geom)),
        "lakes": path(clip(unary_union(lakes))) if lakes else "",
        "places": places,
        "countries": country_labels,
        "riverLabels": river_labels,
        "oceanLabel": dict(zip(("x", "y"), xy(lon0 + 0.35, lat0 + (lat1 - lat0) * 0.55))) | {"name": "Тихий океан"},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    log(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB, viewBox 0 0 {WIDTH} {height})")


if __name__ == "__main__":
    main()
