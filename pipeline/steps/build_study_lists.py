"""Per-day study lists: what to learn before each trip day.

Reads data/itinerary.json, data/sites_resolved.json (trip-report highlights = target_species),
data/site_species.json (GBIF counts incl. autumn freq_aut / level, step gbif_sites),
data/species_index.json (endemic) and data/species/<id>.json (traits.range_restricted,
colombia.near_endemic if ever present). Writes data/study_lists.json:

  {date: {sites, featured: [{id, why, level, freq_aut}], background: [{id, level, freq_aut}],
          dropped_highlights: [{id, site, reason}], featured_cut: [ids]}}

A day's sites are merged: per species the best site wins (max freq_aut, its level; n_aut summed).
featured = highlights with n_aut >= 1 at a site that lists them (others -> dropped_highlights)
         + endemics with level != rare + range-restricted species with level common/uncommon
         (+ near-endemics with level != rare, when the data has that flag).
why gets "new_for_route" when the species is in no earlier day's featured + background.
Sorted: highlights, endemics, then freq_aut desc; capped at CAP, but highlights and endemics are
never cut (anything cut is listed in featured_cut and in the report).
background = top BG by freq_aut among level "common" not already featured.
Also writes data/sources/study_lists_report.md.

Usage: uv run python run.py study
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DATA, SOURCES, SPECIES_DIR, log, read_json, write_json  # noqa: E402

CAP = 30
BG = 12
RANK = {"common": 2, "uncommon": 1, "rare": 0}


def main() -> None:
    itinerary = read_json(DATA / "itinerary.json")
    sites = {s["id"]: s for s in read_json(DATA / "sites_resolved.json")}
    site_sp = read_json(DATA / "site_species.json")
    index = {s["id"]: s for s in read_json(DATA / "species_index.json")}
    traits: dict[str, dict] = {}
    for p in SPECIES_DIR.glob("*.json"):
        sp = json.loads(p.read_text())
        traits[sp["id"]] = {"rr": (sp.get("traits") or {}).get("range_restricted") == 1,
                            "near": bool((sp.get("colombia") or {}).get("near_endemic"))}

    out: dict[str, dict] = {}
    seen: set[str] = set()
    rows = []
    for day in sorted(itinerary, key=lambda d: d["date"]):
        ids = [s for s in day.get("sites") or [] if s in sites]
        # merged stats per species: best site by freq_aut
        stats: dict[str, dict] = {}
        per_site: dict[tuple[str, str], int] = {}
        for sid in ids:
            for x in (site_sp.get(sid) or {}).get("species", []):
                per_site[(sid, x["id"])] = x["n_aut"]
                cur = stats.get(x["id"])
                if cur is None or x["freq_aut"] > cur["freq_aut"]:
                    stats[x["id"]] = {"freq_aut": x["freq_aut"], "level": x["level"],
                                      "n_aut": (cur or {}).get("n_aut", 0) + x["n_aut"]}
                else:
                    cur["n_aut"] += x["n_aut"]

        why: dict[str, list[str]] = {}
        dropped = []
        hl_sites: dict[str, list[str]] = {}
        for sid in ids:
            for t in sites[sid].get("target_species", []):
                hl_sites.setdefault(t, []).append(sid)
        for t, ss in hl_sites.items():
            if any(per_site.get((sid, t), 0) >= 1 for sid in ss):
                why.setdefault(t, []).append("highlight")
            else:
                dropped += [{"id": t, "site": sid, "reason": "no autumn records within radius"} for sid in ss]
        for k, st in stats.items():
            lvl = st["level"]
            if index.get(k, {}).get("endemic") and lvl != "rare":
                why.setdefault(k, []).append("endemic")
            elif traits.get(k, {}).get("near") and lvl != "rare":
                why.setdefault(k, []).append("near_endemic")
            if traits.get(k, {}).get("rr") and lvl in ("common", "uncommon"):
                why.setdefault(k, []).append("range_restricted")

        def st(k: str) -> dict:
            return stats.get(k) or {"freq_aut": 0.0, "level": "rare"}

        featured = [{"id": k, "why": w, "level": st(k)["level"], "freq_aut": st(k)["freq_aut"]} for k, w in why.items()]
        featured.sort(key=lambda f: ("highlight" not in f["why"], "endemic" not in f["why"], -f["freq_aut"], f["id"]))
        protected = sum(1 for f in featured if {"highlight", "endemic"} & set(f["why"]))
        keep = max(CAP, protected)
        cut = [f["id"] for f in featured[keep:]]
        over = len(featured) - CAP
        featured = featured[:keep]
        fids = {f["id"] for f in featured} | set(cut)
        background = sorted(({"id": k, "level": v["level"], "freq_aut": v["freq_aut"]}
                             for k, v in stats.items() if v["level"] == "common" and k not in fids),
                            key=lambda b: (-b["freq_aut"], b["id"]))[:BG]
        for f in featured:
            if f["id"] not in seen:
                f["why"].append("new_for_route")
        seen |= {f["id"] for f in featured} | {b["id"] for b in background}
        out[day["date"]] = {"sites": ids, "featured": featured, "background": background,
                            "dropped_highlights": dropped, "featured_cut": cut}
        rows.append((day["date"], ids, len(featured), len(background), len(dropped), max(over, 0), protected, cut))

    write_json(DATA / "study_lists.json", out)

    def en(k: str) -> str:
        return index.get(k, {}).get("en") or k

    md = ["# Study lists report", "",
          "Generated by `pipeline/steps/build_study_lists.py` from GBIF autumn (Sep-Nov) counts.", "",
          f"Featured cap {CAP} (highlights and endemics are never cut); background = top {BG} common.", "",
          "| Date | Sites | Featured | Background | Dropped highlights | Over cap |", "|---|---|---|---|---|---|"]
    for d, ids, nf, nb, nd, over, prot, cut in rows:
        md.append(f"| {d} | {', '.join(ids) or '-'} | {nf} | {nb} | {nd} | {over or ''} |")
    md += ["", "## Over the cap", ""]
    for d, ids, nf, nb, nd, over, prot, cut in rows:
        if over:
            md.append(f"- {d}: {nf + len(cut)} candidates, {over} over {CAP}; {prot} highlights+endemics kept; "
                      f"cut {len(cut)}: {', '.join(en(c) for c in cut) or '-'}")
    md += ["", "## Dropped highlights (no autumn GBIF records within the site radius)", ""]
    for d, v in out.items():
        for x in v["dropped_highlights"]:
            md.append(f"- {d} · {sites[x['site']]['name']} · {en(x['id'])} (*{index.get(x['id'], {}).get('sci', '')}*)")
    (SOURCES / "study_lists_report.md").write_text("\n".join(md) + "\n")
    n_over = sum(1 for r in rows if r[5])
    log(f"days: {len(rows)}, featured per day max {max(r[2] for r in rows)}, days over cap {n_over}, "
        f"dropped highlights {sum(r[4] for r in rows)}")


if __name__ == "__main__":
    main()
