"""Page numbers of every species in the Lynx field guide "Birds of Colombia" (Hilty 2021).

The tour group carries Steven L. Hilty, *Birds of Colombia* (Lynx and BirdLife International Field
Guides, Lynx Edicions, Barcelona, 2021). The owner photographed its "English and Scientific Index"
(book pages 559-590; p591, the first page of the Spanish index, is kept as a partial extra), "References and further reading" (555-557) and "Family index" (605; p604 holds only cut-off ends of lines of another group index); Claude
agents transcribed the photos into plain text under pipeline/sources/lynx/ (format: one index entry per
line, `## page N` / `## column N` headers, bold English group headings as `**Heading**`, indented
sub-entries, family names in capitals, `??` = unreadable, `## notes` at the end of a page).

Outputs:
- data/sources/lynx_index.json: every parsed index entry ({text, page_in_index, kind, pages, first_page, ...}).
- data/sources/lynx_references.json: [{page, text}] from references.txt.
- data/sources/lynx_families.json: [{name, page, pages?, fragment?}] from family_index.txt + p604_fragment.txt
  (p604: cut-off line ends of a group index, names start with "...", `fragment: true`; not family names).
- data/lynx_pages.json: {slug: {page, sci: {page, entry, via}, en: {page, entry, via}, conflict}} for every
  species in data/species_index.json. Scientific match: (genus, epithet) exact; else
  pipeline/mappings/lynx_names.json ({site sci: book sci or book English name}); else the same epithet
  within the same family (genus moves, `via: "epithet"`). English match: normalised full name (case,
  hyphens, spaces, apostrophes, diacritics, British/American spelling), eBird name first, then ACO's.
  `page` = sci page, else en page; `conflict` = both found and different.
- data/sources/lynx_unmatched.json and data/sources/lynx_report.md: counts, conflicts, unmatched species by
  family and near-miss suggestions (same genus, epithet within edit distance 2) for the mapping file.

Run after `build` (needs data/species_index.json); re-run `build` afterwards to merge `lynx_page` into the
species files, species_index.json and families.json.

Index entry syntax (Lynx): `epithet, Genus page` or `epithet, Genus (species) page`; the parenthesised
word is the species in which the book places that taxon as a subspecies/group (e.g. `andinus, Sclerurus
(mexicanus)`), stored as `subspecies` as printed. Options: --src DIR (default pipeline/sources/lynx),
--out DIR (default data/; sources files go to DIR/sources), used by tests and dry runs.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, PIPELINE, SPECIES_DIR, log, read_json, write_json, write_text  # noqa: E402

SRC = PIPELINE / "sources" / "lynx"
MAPPING = PIPELINE / "mappings" / "lynx_names.json"

BOOK = {
    "title": "Birds of Colombia",
    "authors": ["Steven L. Hilty"],
    "publisher": "Lynx Edicions, Barcelona",
    "year": 2021,
    "series": "Lynx and BirdLife International Field Guides",
    "edition_note": "1st edition, 608 pp., 1,965 species; flexibound and hardcover",
    "isbn": {"flexi": "978-84-16728-24-4", "hardcover": "978-84-16728-23-7"},
    "pages_total": 608,
    "species_count": 1965,
    "pages": {"index": [559, 590], "spanish_index_first_page": 591, "references": [555, 557], "family_index": 605},
    "transcribed": "2026-09-27",
    "method": "photographed by the owner, transcribed by Claude agents from the photos",
}

# ---------------------------------------------------------------- parsing

_TOKEN = r"[\d?]{1,3}(?:\s*[–-]\s*[\d?]{1,3})?"
PAGES_RE = re.compile(rf"\s+({_TOKEN}(?:\s*,\s*{_TOKEN})*)\s*$")
BOLD_RE = re.compile(r"^\*\*(.+?)\*\*(.*)$")
SCI_RE = re.compile(r"^([a-z][a-z'-]*),\s+([A-Z][a-z]+)(?:\s+\(([^)]*)\))?$")
GENUS_RE = re.compile(r"^[A-Z][a-z]+$")
FAMILY_RE = re.compile(r"^[A-Z]{4,}$")


def parse_pages(s: str) -> list[list[int]]:
    """'366, 379–391' -> [[366, 366], [379, 391]]; tokens with '??' are dropped; '379–91' -> [379, 391]."""
    out = []
    for tok in s.split(","):
        parts = [x.strip() for x in re.split(r"[–-]", tok.strip(), maxsplit=1)]
        if not parts[0] or any("?" in x or not x.isdigit() for x in parts):
            continue
        a, b = parts[0], parts[-1]
        if len(b) < len(a) and int(b) < int(a):  # abbreviated range end
            b = a[: len(a) - len(b)] + b
        out.append([int(a), int(b)])
    return out


def split_pages(body: str) -> tuple[str, list[list[int]], bool]:
    """Split trailing page references off an entry: (text, ranges, had_page_field)."""
    m = PAGES_RE.search(body)
    if not m or not re.search(r"\d|\?\?", m.group(1)):
        return body.strip(), [], False
    return body[: m.start()].strip(), parse_pages(m.group(1)), True


def _entry(text: str, page: int, kind: str, pages: list[list[int]], **kw) -> dict:
    e = {"text": text, "page_in_index": page, "kind": kind, "pages": pages,
         "first_page": pages[0][0] if pages else None}
    e.update(kw)
    if "??" in text:
        e["uncertain"] = True
    return e


def parse_index_files(files: list[Path]) -> tuple[list[dict], dict[int, list[str]]]:
    """Parse index page files (sorted by page). The current bold heading persists across columns and
    pages and changes only on a new `**heading**`; sub-entries continuing a heading from a page that is
    not the immediately preceding one (a missing transcription) get `group_uncertain`."""
    entries: list[dict] = []
    notes: dict[int, list[str]] = {}
    group: str | None = None
    prev_page: int | None = None
    for f in files:
        m = re.search(r"(\d+)", f.stem)
        page = int(m.group(1)) if m else 0
        carried = group is not None and prev_page is not None and page == prev_page + 1
        from_prev_page = True  # until the first heading on this page
        in_notes = False
        for raw in f.read_text(encoding="utf-8").splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            if line.startswith("## notes"):
                in_notes = True
                continue
            if in_notes:
                notes.setdefault(page, []).append(line.strip())
                continue
            hm = re.match(r"^## page\s+(\d+)", line)
            if hm:
                if int(hm.group(1)) != page:
                    log(f"  WARNING: {f.name} says page {hm.group(1)}")
                    page = int(hm.group(1))
                continue
            if line.startswith("#"):  # column headers, letter headers (# A)
                continue
            if line.startswith(" "):
                qual, pages, _ = split_pages(line.strip())
                extra = {}
                if group is None:
                    extra["orphan"] = True
                elif from_prev_page and not carried:
                    extra["group_uncertain"] = True
                name = f"{qual} {group}" if group else qual
                entries.append(_entry(line, page, "en", pages, group=group, qualifier=qual, name=name, **extra))
                continue
            bm = BOLD_RE.match(line.strip())
            if bm:
                head, rest = bm.group(1).strip(), bm.group(2)
                group, from_prev_page = head, False
                if rest.strip().startswith(","):  # `**Antpipit**, Ringed 365`: heading + inline sub-entry
                    qual, pages, _ = split_pages(rest.strip()[1:])
                    entries.append(_entry(line, page, "en", pages, group=head, qualifier=qual, name=f"{qual} {head}"))
                else:
                    _, pages, has = split_pages(" " + rest)
                    if has:  # `**Anhinga** 149`: a name of its own and the group for what follows
                        entries.append(_entry(line, page, "en", pages, group=head, qualifier=None, name=head))
                    else:
                        entries.append(_entry(line, page, "en_group", [], group=head))
                continue
            body, pages, _ = split_pages(line.strip())
            sm = SCI_RE.match(body)
            if sm:
                entries.append(_entry(line, page, "sci", pages, genus=sm.group(2), epithet=sm.group(1),
                                      subspecies=(sm.group(3) or None)))
            elif FAMILY_RE.match(body):
                entries.append(_entry(line, page, "family", pages, family=body.title()))
            elif GENUS_RE.match(body):
                entries.append(_entry(line, page, "genus", pages, genus=body))
            else:
                entries.append(_entry(line, page, "other", pages))
        prev_page = page
    return entries, notes


def parse_references(path: Path) -> list[dict]:
    out, page = [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## notes"):
            break
        m = re.match(r"^## page\s+(\d+)", line)
        if m:
            page = int(m.group(1))
            continue
        if line.startswith("#"):
            continue
        out.append({"page": page, "text": line})
    return out


def parse_families(path: Path, fragment: bool = False) -> list[dict]:
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## notes"):
            break
        if line.startswith("#") or line.startswith("[gap"):
            continue
        name, ranges, _ = split_pages(line.replace("**", ""))
        rec: dict = {"name": name, "page": ranges[0][0] if ranges else None}
        if ranges and (len(ranges) > 1 or ranges[0][0] != ranges[0][1]):
            rec["pages"] = [min(r[0] for r in ranges), max(r[1] for r in ranges)]
        if "??" in line or not ranges:
            rec["uncertain"] = True
        if fragment:
            rec["fragment"] = True
        out.append(rec)
    return out


# ---------------------------------------------------------------- matching

SPELLING = [("grey", "gray"), ("colour", "color"), ("moustache", "mustache"), ("sombre", "somber"),
            ("centre", "center"), ("ochre", "ocher"), ("sulphur", "sulfur")]


def norm_en(name: str) -> str:
    """Lower-case, no diacritics, British -> American spelling, no hyphens/spaces/apostrophes."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    for uk, us in SPELLING:
        s = s.replace(uk, us)
    return re.sub(r"[\s\-'’.]+", "", s)


def norm_word(w: str) -> str:
    return unicodedata.normalize("NFKD", w).encode("ascii", "ignore").decode().lower().strip()


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _best(entries: list[dict]) -> dict:
    """Prefer the species-level line (no parenthesised species) and a readable one."""
    return sorted(entries, key=lambda e: (e.get("subspecies") is not None, bool(e.get("uncertain")),
                                          e["first_page"] is None))[0]


def match_species(species: list[dict], entries: list[dict], mapping: dict[str, str],
                  en_aco: dict[str, str] | None = None) -> tuple[dict, dict]:
    """Return ({slug: record}, extra info for the report)."""
    en_aco = en_aco or {}
    sci_idx: dict[tuple[str, str], list[dict]] = defaultdict(list)
    en_idx: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        if e["kind"] == "sci" and e["first_page"] is not None:
            sci_idx[(norm_word(e["genus"]), norm_word(e["epithet"]))].append(e)
        elif e["kind"] == "en" and e["first_page"] is not None and not e.get("orphan"):
            en_idx[norm_en(e["name"])].append(e)

    def split(sci: str) -> tuple[str, str]:
        g, _, ep = sci.partition(" ")
        return norm_word(g), norm_word(ep.split()[0] if ep else "")

    def en_lookup(name: str | None) -> dict | None:
        return _best(en_idx[norm_en(name)]) if name and en_idx.get(norm_en(name)) else None

    out: dict[str, dict] = {}
    used: set[tuple[str, str]] = set()
    pending: list[dict] = []
    for sp in species:
        key = split(sp["sci"])
        rec = {"sci": {"page": None, "entry": None}, "en": {"page": None, "entry": None}}
        if key in sci_idx:
            e = _best(sci_idx[key])
            rec["sci"] = {"page": e["first_page"], "entry": e["text"], "via": "exact"}
            used.add(key)
        elif sp["sci"] in mapping:
            target = mapping[sp["sci"]]
            if re.match(r"^[A-Z][a-z]+ [a-z'-]+$", target.strip()):
                k2 = split(target.strip())
                if k2 in sci_idx:
                    e = _best(sci_idx[k2])
                    rec["sci"] = {"page": e["first_page"], "entry": e["text"], "via": "mapping"}
                    used.add(k2)
                else:
                    log(f"  WARNING: mapping {sp['sci']} -> {target}: not in the book index")
            else:
                e = en_lookup(target)
                if e:
                    rec["sci"] = {"page": e["first_page"], "entry": e["text"], "via": "mapping"}
                else:
                    log(f"  WARNING: mapping {sp['sci']} -> {target}: not in the book index")
        if rec["sci"]["page"] is None:
            pending.append(sp)
        e, via = en_lookup(sp.get("en")), "ebird"
        if not e and en_aco.get(sp["id"]) and en_aco[sp["id"]] != sp.get("en"):
            e, via = en_lookup(en_aco[sp["id"]]), "aco"
        if e:
            rec["en"] = {"page": e["first_page"], "entry": e["text"], "via": via}
        out[sp["id"]] = rec

    # Genus moves: same epithet, same family. A book genus belongs to a family when the site has that
    # genus in it, or when its page lies within the page span of the family's exact matches.
    fam_of_genus: dict[str, set[str]] = defaultdict(set)
    span: dict[str, list[int]] = {}
    for sp in species:
        g, _ = split(sp["sci"])
        fam_of_genus[g].add(sp["family"])
        p = out[sp["id"]]["sci"]["page"]
        if p is not None and out[sp["id"]]["sci"].get("via") == "exact":
            s = span.setdefault(sp["family"], [p, p])
            s[0], s[1] = min(s[0], p), max(s[1], p)
    by_epithet: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for k in sci_idx:
        by_epithet[k[1]].append(k)

    def in_family(k: tuple[str, str], fam: str) -> bool:
        if fam in fam_of_genus.get(k[0], ()):
            return True
        s, p = span.get(fam), sci_idx[k][0]["first_page"]
        return bool(s) and s[0] - 1 <= p <= s[1] + 1

    for sp in pending:
        _, ep = split(sp["sci"])
        cands = [k for k in by_epithet.get(ep, []) if k not in used and in_family(k, sp["family"])]
        if len(cands) == 1:
            e = _best(sci_idx[cands[0]])
            out[sp["id"]]["sci"] = {"page": e["first_page"], "entry": e["text"], "via": "epithet"}

    for rec in out.values():
        sp_, en_ = rec["sci"]["page"], rec["en"]["page"]
        rec["page"] = sp_ if sp_ is not None else en_
        rec["conflict"] = sp_ is not None and en_ is not None and sp_ != en_

    # Near misses for unmatched species: same genus, epithet within edit distance 2 (never auto-applied).
    near: dict[str, list[str]] = {}
    by_genus: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for k in sci_idx:
        by_genus[k[0]].append(k)
    for sp in species:
        if out[sp["id"]]["sci"]["page"] is None:
            g, ep = split(sp["sci"])
            hits = [k for k in by_genus.get(g, []) if levenshtein(k[1], ep) <= 2]
            if hits:
                near[sp["id"]] = [f"{sci_idx[k][0]['genus']} {sci_idx[k][0]['epithet']} ({sci_idx[k][0]['first_page']})"
                                  for k in hits]
    return out, {"near": near, "book_species": len(sci_idx), "book_unused": sorted(set(sci_idx) - used)}


# ---------------------------------------------------------------- report

def report(species: list[dict], pages: dict, extra: dict, families: dict[str, str], out_path: Path) -> dict:
    n = len(species)
    both = [s for s in species if pages[s["id"]]["sci"]["page"] is not None and pages[s["id"]]["en"]["page"] is not None]
    sci_only = [s for s in species if pages[s["id"]]["sci"]["page"] is not None and pages[s["id"]]["en"]["page"] is None]
    en_only = [s for s in species if pages[s["id"]]["sci"]["page"] is None and pages[s["id"]]["en"]["page"] is not None]
    unmatched = [s for s in species if pages[s["id"]]["page"] is None]
    epithet = [s for s in species if pages[s["id"]]["sci"].get("via") == "epithet"]
    mapped = [s for s in species if pages[s["id"]]["sci"].get("via") == "mapping"]
    conflicts = [s for s in species if pages[s["id"]]["conflict"]]
    counts = {"total": n, "both": len(both), "sci_only": len(sci_only), "en_only": len(en_only),
              "epithet": len(epithet), "mapping": len(mapped), "unmatched": len(unmatched), "conflicts": len(conflicts)}
    lines = [
        "# Lynx «Birds of Colombia» (Hilty 2021): index match report",
        "",
        "Generated by `pipeline/steps/build_lynx.py` (step `lynx`). Add taxonomy differences to "
        "`pipeline/mappings/lynx_names.json` (`{\"<site sci name>\": \"<book sci name or English name>\"}`) and re-run "
        "`uv run python run.py lynx build`.",
        "",
        f"- Species on the site: {n}",
        f"- Matched by both scientific and English name: {len(both)}",
        f"- Scientific name only: {len(sci_only)}",
        f"- English name only: {len(en_only)}",
        f"- Scientific match via epithet within the family (genus moves): {len(epithet)}",
        f"- Scientific match via the mapping file: {len(mapped)}",
        f"- No page at all: {len(unmatched)}",
        f"- Conflicts (scientific and English pages differ): {len(conflicts)}",
        f"- Book scientific names (species and subspecies lines) not matched to any site species: {len(extra['book_unused'])}",
        "",
        f"## Conflicts ({len(conflicts)})",
        "",
    ]
    for s in conflicts:
        r = pages[s["id"]]
        lines.append(f"- *{s['sci']}* ({s['en']}): sci `{r['sci']['entry']}` vs en `{r['en']['entry'].strip()}`")
    if not conflicts:
        lines.append("- none")
    lines += ["", f"## Genus moves matched by epithet ({len(epithet)})", ""]
    lines += [f"- *{s['sci']}* ({s['en']}) = `{pages[s['id']]['sci']['entry']}`" for s in epithet] or ["- none"]
    lines += ["", f"## Unmatched species by family ({len(unmatched)})", ""]
    by_fam: dict[str, list[dict]] = defaultdict(list)
    for s in unmatched:
        by_fam[s["family"]].append(s)
    for fam, lst in by_fam.items():
        lines += [f"### {families.get(fam, fam)} ({len(lst)})", ""]
        for s in lst:
            hint = f" — near miss: {', '.join(extra['near'][s['id']])}" if s["id"] in extra["near"] else ""
            lines.append(f"- *{s['sci']}* ({s['en']}){hint}")
        lines.append("")
    near_other = {k: v for k, v in extra["near"].items() if pages[k]["page"] is not None}
    lines += [f"## Near misses of species found only by English name ({len(near_other)})", ""]
    sp_by_id = {s["id"]: s for s in species}
    lines += [f"- *{sp_by_id[k]['sci']}*: {', '.join(v)}" for k, v in near_other.items()] or ["- none"]
    write_text(out_path, "\n".join(lines) + "\n")
    return counts


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    src, out = SRC, DATA
    if "--src" in args:
        src = Path(args[args.index("--src") + 1]).resolve()
    if "--out" in args:
        out = Path(args[args.index("--out") + 1]).resolve()
    sources = out / "sources"

    files = sorted((src / "index").glob("*.txt"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    if not files:
        sys.exit(f"lynx: no index transcriptions in {src / 'index'}")
    entries, notes = parse_index_files(files)
    pages_have = sorted({e["page_in_index"] for e in entries})
    missing = [p for p in range(BOOK["pages"]["index"][0], BOOK["pages"]["index"][1] + 1) if p not in pages_have]
    kinds: dict[str, int] = defaultdict(int)
    for e in entries:
        kinds[e["kind"]] += 1
    log(f"  index: {len(files)} pages, {len(entries)} entries ({', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))}), "
        f"uncertain {sum(1 for e in entries if e.get('uncertain'))}, orphan sub-entries {sum(1 for e in entries if e.get('orphan'))}")
    if missing:
        log(f"  WARNING: index pages not transcribed yet: {missing}")
    spanish_files = sorted((src / "spanish_index").glob("*.txt"))
    spanish = None
    if spanish_files:  # only the first page of the Spanish index was photographed: kept, not matched
        sp_entries, _ = parse_index_files(spanish_files)
        spanish = {"partial": True, "pages": [e for e in sorted({x["page_in_index"] for x in sp_entries})],
                   "entries": sp_entries}
        log(f"  spanish index (partial): {len(sp_entries)} entries")
    write_json(sources / "lynx_index.json", {"book": BOOK, "pages_missing": missing,
                                             "notes": {str(k): v for k, v in notes.items()}, "entries": entries,
                                             "spanish": spanish})

    if (src / "references.txt").exists():
        refs = parse_references(src / "references.txt")
        write_json(sources / "lynx_references.json", refs)
        log(f"  references: {len(refs)}")
    else:
        log("  WARNING: references.txt missing")
    fams: list[dict] = []
    if (src / "p604_fragment.txt").exists():
        fams += parse_families(src / "p604_fragment.txt", fragment=True)
    if (src / "family_index.txt").exists():
        fams += parse_families(src / "family_index.txt")
    if fams:
        write_json(sources / "lynx_families.json", fams)
        log(f"  families: {len(fams)} ({sum(1 for f in fams if f.get('fragment'))} from the p604 fragment)")
    else:
        log("  WARNING: family_index.txt missing")

    species = read_json(DATA / "species_index.json")
    if not species:
        sys.exit("lynx: data/species_index.json missing, run `build` first")
    mapping = {k: v for k, v in (read_json(MAPPING) or {}).items() if not k.startswith("_")}
    en_aco = {}
    for sp in species:
        rec = read_json(SPECIES_DIR / f"{sp['id']}.json") or {}
        if rec.get("names", {}).get("en_aco"):
            en_aco[sp["id"]] = rec["names"]["en_aco"]
    pages, extra = match_species(species, entries, mapping, en_aco)
    write_json(out / "lynx_pages.json", pages)
    unmatched = [{"id": s["id"], "sci": s["sci"], "en": s["en"], "family": s["family"],
                  "near_miss": extra["near"].get(s["id"], [])} for s in species if pages[s["id"]]["page"] is None]
    write_json(sources / "lynx_unmatched.json", unmatched)
    fam_names = {f["code"]: f"{f['names'].get('en')} ({f['sci']})" for f in (read_json(DATA / "families.json") or [])}
    c = report(species, pages, extra, fam_names, sources / "lynx_report.md")
    log(f"  species {c['total']}: both {c['both']}, sci only {c['sci_only']}, en only {c['en_only']} "
        f"(epithet {c['epithet']}, mapping {c['mapping']}), unmatched {c['unmatched']}, conflicts {c['conflicts']}")


if __name__ == "__main__":
    main()
