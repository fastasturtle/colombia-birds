"""Resolve hand-authored site targets to species ids.

Reads data/sites.json (hand-authored) and data/species_index.json; writes
data/sites_resolved.json (sites + target_species / unmatched_targets),
data/focus_species.json (sorted unique resolved ids) and
data/region_species.json (ACO species whose elevation range overlaps each region's band).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DATA, SPECIES_DIR, log, norm_sci, read_json, write_json  # noqa: E402


def norm_en(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"['’`]", "", s)
    s = re.sub(r"[-\s]+", " ", s).strip()
    return re.sub(r"\bgrey\b", "gray", s)


def build_lookups(index: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    by_sci: dict[str, str] = {}
    by_en: dict[str, str] = {}
    for sp in index:
        by_sci[norm_sci(sp["sci"])] = sp["id"]
        if sp.get("en"):
            by_en[norm_en(sp["en"])] = sp["id"]
    for path in sorted(SPECIES_DIR.glob("*.json")):
        sp = json.loads(path.read_text())
        for key in ("sci_name_aco", "sci_name"):
            if sp.get(key):
                by_sci.setdefault(norm_sci(sp[key]), sp["id"])
        for key in ("en", "en_aco"):
            en = (sp.get("names") or {}).get(key)
            if en:
                by_en.setdefault(norm_en(en), sp["id"])
    return by_sci, by_en


def sci_candidates(sci: str) -> list[str]:
    parts = norm_sci(sci).split()
    if len(parts) >= 3:  # trinomial: subspecies may be split to species, else fall back to binomial
        return [f"{parts[0]} {parts[-1]}", f"{parts[0]} {parts[1]}"]
    return [" ".join(parts)]


def resolve(t: dict, by_sci: dict, by_en: dict, genera: set) -> tuple[str | None, str]:
    if t.get("sci"):
        for c in sci_candidates(t["sci"]):
            if c in by_sci:
                return by_sci[c], "sci"
    if t.get("en") and norm_en(t["en"]) in by_en:
        return by_en[norm_en(t["en"])], "en"
    if t.get("sci") and norm_sci(t["sci"]).split()[0] not in genera:
        return None, "genus not in species index"
    return None, "not in ACO Colombia list (by sci or en)" if t.get("sci") else "no match by en (no sci given)"


def elev(sp: dict) -> tuple[int, int] | None:
    """BIRDBASE range; 'L' (lowlands) as min -> 0, as max -> 500; other codes are unusable."""
    lo, hi = sp.get("elev") or (None, None)
    lo = 0 if lo == "L" else lo
    hi = 500 if hi == "L" else hi
    return (lo, hi) if isinstance(lo, int) and isinstance(hi, int) else None


REGION_BANDS: dict[str, tuple[int, int]] = {}  # filled from sites


def main() -> None:
    sites = read_json(DATA / "sites.json")
    index = read_json(DATA / "species_index.json")
    by_sci, by_en = build_lookups(index)
    genera = {k.split()[0] for k in by_sci}
    focus: set[str] = set()
    n_ok = n_bad = 0
    for site in sites:
        ids, unmatched = [], []
        for t in site.get("target_species_raw", []):
            sid, how = resolve(t, by_sci, by_en, genera)
            if sid:
                if sid not in ids:
                    ids.append(sid)
                n_ok += 1
            else:
                unmatched.append({**t, "reason": how})
                log(f"  unmatched [{site['id']}] {t['en']} / {t.get('sci')}: {how}")
                n_bad += 1
        site["target_species"] = ids
        site["unmatched_targets"] = unmatched
        focus.update(ids)
        lo, hi = REGION_BANDS.get(site["region"], (10**6, -1))
        REGION_BANDS[site["region"]] = (min(lo, site["elev_min"]), max(hi, site["elev_max"]))
    write_json(DATA / "sites_resolved.json", sites)
    write_json(DATA / "focus_species.json", sorted(focus))

    # Species (ACO list = species_index) whose elevation range overlaps each region's site band.
    region_species = {
        r: sorted(sp["id"] for sp in index if (e := elev(sp)) and e[0] <= hi and e[1] >= lo)
        for r, (lo, hi) in REGION_BANDS.items()
    }
    write_json(DATA / "region_species.json",
               {r: {"elev_band": list(REGION_BANDS[r]), "species": ids} for r, ids in region_species.items()})
    log(f"sites: {len(sites)}, targets resolved: {n_ok}, unmatched: {n_bad}, focus species: {len(focus)}")
    for r, ids in region_species.items():
        log(f"  region {r} {REGION_BANDS[r]}: {len(ids)} species")


if __name__ == "__main__":
    main()
