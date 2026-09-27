"""Wikipedia plain-text extracts (CC BY-SA 4.0) for en/es/ru -> data/texts/<slug>.json

Stores the intro and named sections (Description, Distribution and habitat, Behaviour, ...) per language,
with title, URL, revision id and retrieval date for attribution. Text is CC BY-SA 4.0; any derived text
on the site must credit the article and carry the same license.
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (  # noqa: E402
    DATA, SPECIES_DIR, fmt_elapsed, get_json, log, only_slugs, read_json, status, time_up, write_json,
)

TEXTS = DATA / "texts"
LANGS = ("en", "es", "ru")
SECTION_RE = re.compile(r"^(={2,4})\s*(.+?)\s*\1\s*$", re.M)


def split_sections(text: str) -> tuple[str, dict[str, str]]:
    """explaintext with exsectionformat=wiki gives '== Heading ==' lines."""
    parts = SECTION_RE.split(text)
    intro = parts[0].strip()
    sections: dict[str, str] = {}
    # parts: [intro, '==', 'Heading', body, '==', 'Heading', body, ...]
    for i in range(1, len(parts) - 2, 3):
        level, heading, body = parts[i], parts[i + 1], parts[i + 2].strip()
        if level == "==" and body:
            sections[heading] = body
        elif level != "==" and body:
            # fold subsections into the last top-level section
            if sections:
                last = list(sections)[-1]
                sections[last] += f"\n\n{heading}\n{body}"
            else:
                sections[heading] = body
    return intro, sections


def fetch(lang: str, title: str) -> dict | None:
    data = get_json(
        f"https://{lang}.wikipedia.org/w/api.php",
        {
            "action": "query",
            "prop": "extracts|revisions",
            "explaintext": 1,
            "exsectionformat": "wiki",
            "rvprop": "ids",
            "redirects": 1,
            "titles": title,
            "format": "json",
            "formatversion": 2,
        },
        kind="wikipedia",
        min_interval=1.0,
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None
    p = pages[0]
    text = p.get("extract", "")
    if not text:
        return None
    intro, sections = split_sections(text)
    drop = {"References", "External links", "See also", "Further reading", "Notes", "Sources", "Gallery",
            "Referencias", "Enlaces externos", "Véase también", "Bibliografía", "Notas",
            "Примечания", "Ссылки", "Литература", "См. также", "Галерея"}
    sections = {k: v for k, v in sections.items() if k not in drop}
    return {
        "title": p["title"],
        "url": f"https://{lang}.wikipedia.org/wiki/{p['title'].replace(' ', '_')}",
        "revision": (p.get("revisions") or [{}])[0].get("revid"),
        "retrieved": dt.date.today().isoformat(),
        "license": "CC BY-SA 4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "intro": intro,
        "sections": sections,
    }


def main() -> None:
    only = only_slugs(sys.argv[1:])
    files = sorted(SPECIES_DIR.glob("*.json"))
    total = len(only) if only else len(files)
    done = fetched = skipped = 0
    for f in files:
        if only and f.stem not in only:
            continue
        if time_up("wikipedia"):
            break
        sp = read_json(f)
        out_path = TEXTS / f"{sp['id']}.json"
        existing = read_json(out_path, {})
        rec = {"id": sp["id"], "wikipedia": existing.get("wikipedia", {})}
        n_before = len(rec["wikipedia"])
        for lang in LANGS:
            url = sp["links"]["wikipedia"].get(lang)
            if not url or lang in rec["wikipedia"]:
                continue
            title = url.rsplit("/wiki/", 1)[-1].replace("_", " ")
            from urllib.parse import unquote
            title = unquote(title)
            try:
                got = fetch(lang, title)
            except Exception as e:  # keep going; rerun picks up the gaps
                log(f"  {sp['id']} {lang}: {e}")
                continue
            if got:
                rec["wikipedia"][lang] = got
        if len(rec["wikipedia"]) > n_before:
            write_json(out_path, rec)  # written per species, so an interrupted run keeps what it fetched
            fetched += 1
        else:
            skipped += 1
        done += 1
        if done % 100 == 0:
            status("wikipedia", done, total, f"wikipedia: {done}/{total} species, {fetched} updated, "
                   f"{skipped} unchanged/skipped, elapsed {fmt_elapsed()}")
    n = sum(1 for _ in TEXTS.glob("*.json"))
    status("wikipedia", done, total, f"wikipedia: texts for {n} species ({done}/{total} processed this run)")


if __name__ == "__main__":
    main()
