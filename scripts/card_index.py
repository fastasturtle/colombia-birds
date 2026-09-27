#!/usr/bin/env python3
"""Fact-check index of species cards: writes docs/fact-check/INDEX.md.

Reads the `checked:` date (YYYY-MM-DD) from the frontmatter of content/species/*.md,
names from data/species_index.json and groups from data/groups.json (via family code).
Plain Python 3, no dependencies. Output is sorted and has no timestamp, so a rerun
without card changes produces no diff.

Usage (from anywhere): python3 scripts/card_index.py
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "content" / "species"
OUT = ROOT / "docs" / "fact-check" / "INDEX.md"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def checked_date(path: Path) -> str | None:
    """Top-level `checked:` value, or None if absent/null; exits on an invalid value."""
    for line in frontmatter(path.read_text(encoding="utf-8")).splitlines():
        m = re.match(r"^checked:\s*(.*?)\s*(#.*)?$", line)
        if not m:
            continue
        v = m.group(1).strip("'\"")
        if v in ("", "null", "~"):
            return None
        try:
            valid = bool(DATE.match(v)) and datetime.date.fromisoformat(v).isoformat() == v
        except ValueError:
            valid = False
        if not valid:
            sys.exit(f"{path.relative_to(ROOT)}: checked must be YYYY-MM-DD, got {v!r}")
        return v
    return None


def main() -> None:
    index = {s["id"]: s for s in json.loads((ROOT / "data" / "species_index.json").read_text(encoding="utf-8"))}
    groups = json.loads((ROOT / "data" / "groups.json").read_text(encoding="utf-8"))
    group_of = {fam: (i, g["name_ru"]) for i, g in enumerate(groups) for fam in g["families"]}

    rows = []
    for path in sorted(CARDS.glob("*.md")):
        slug = path.stem
        sp = index.get(slug, {})
        gi, gname = group_of.get(sp.get("family"), (len(groups), "—"))
        rows.append({"slug": slug, "en": sp.get("en", "?"), "group": gname,
                     "key": (gi, sp.get("taxon_order", 1e9), slug), "checked": checked_date(path)})

    checked = sorted((r for r in rows if r["checked"]), key=lambda r: (r["checked"], r["key"]))
    unchecked = sorted((r for r in rows if not r["checked"]), key=lambda r: r["key"])

    out = [
        "# Факт-чек карточек видов: указатель",
        "",
        "Генерируется `scripts/card_index.py` из поля `checked:` в `content/species/*.md`; руками не править.",
        "Журнал проверок: `docs/fact-check-log.md`.",
        "",
        f"- Карточек: {len(rows)}",
        f"- Проверено: {len(checked)}",
        f"- Не проверено: {len(unchecked)}",
        "",
        f"## Не проверено ({len(unchecked)})",
        "",
        "| Слаг | English | Группа |",
        "|---|---|---|",
        *(f"| {r['slug']} | {r['en']} | {r['group']} |" for r in unchecked),
        "",
        f"## Проверено ({len(checked)})",
        "",
        "| Слаг | English | Группа | Дата |",
        "|---|---|---|---|",
        *(f"| {r['slug']} | {r['en']} | {r['group']} | {r['checked']} |" for r in checked),
        "",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} cards, {len(checked)} checked, {len(unchecked)} unchecked")


if __name__ == "__main__":
    main()
