#!/usr/bin/env python3
"""Word frequencies for the birder's-English vocabulary (content/vocabulary.yaml, page /words/).

Counts in how many English species names (data/species_index.json, field `en`) and in how many species' English
Wikipedia texts (data/texts/*.json: `wikipedia.en.intro` plus all `wikipedia.en.sections`) a word occurs. It is a
document frequency: a word counted once per name and once per species text, however often it repeats there.
Hyphens count as spaces ("Chestnut-crowned" -> chestnut, crowned).

Usage (stdlib only):
  python3 scripts/vocab_freq.py [--top N] [--intro-only]    top words: word, names, texts, total (stopwords dropped)
  python3 scripts/vocab_freq.py --word rump "wing bar"       counts and example species for given terms
  python3 scripts/vocab_freq.py --fill content/vocabulary.yaml
      rewrite `freq:` and `examples:` of every entry in the vocabulary file (keeps everything else)

Terms match their simple inflections: rump -> rumps, rumped; bar -> bars, barred; belly -> bellied; wing bar -> wing-bars.
`freq` = names + texts. `examples` = up to 3 species whose English name contains the term: regular species before
vagrants and introduced ones, names ending in the term first ("Barred Hawk" before "Hawk-Eagle"), then focus species
of the route (data/focus_species.json). An entry written with `examples: []` keeps it empty (the names use the word
in another sense, e.g. edge -> Pale-edged).
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN = re.compile(r"[a-z]+")

STOP = set("""
a about above after again against all almost also although always am among an and any are as at be because been
before being below between both but by can could did do does during each either else even ever every few for from
further had has have having he her here hers him his how however i if in into is it its itself just least less
many may more most much must my neither no nor not now of off often on once one only or other others our out over
own per rather same she should since so some such than that the their them then there these they this those though
through thus to too under until up upon us very was we were what when where whether which while who whom whose why
will with within without would yet you your known two three four five six called named name names species genus
family bird birds first found include includes including described description subspecies recognised recognized
considered well mostly usually sometimes generally especially commonly common
""".split())


RARE = set()  # vagrant, hypothetical, introduced or extinct: never picked as examples first


def norm(text):
    return re.sub(r"[-‐-―]", " ", text.lower())


def load():
    index = json.loads((ROOT / "data/species_index.json").read_text())
    names = [(s["id"], norm(s.get("en") or "")) for s in index]
    RARE.update(s["id"] for s in index if not {"resident", "endemic", "boreal_migrant", "austral_migrant"} & set(s.get("status") or []) or "extinct" in (s.get("status") or []))
    texts, intros = [], []
    for f in sorted((ROOT / "data/texts").glob("*.json")):
        try:
            en = ((json.loads(f.read_text()).get("wikipedia") or {}).get("en") or {})
        except json.JSONDecodeError:
            continue
        parts = [en.get("intro") or ""] + [v for v in (en.get("sections") or {}).values() if isinstance(v, str)]
        intros.append(norm(en.get("intro") or ""))
        texts.append(norm(" ".join(parts)))
    return names, texts, intros


def term_re(term):
    def one(w):
        forms = re.escape(w) + r"(?:s|es|d|ed|[bdgmnprt]ed|ing)?"
        if w.endswith("y"):  # belly -> bellied, bellies
            forms = f"(?:{forms}|{re.escape(w[:-1])}(?:ied|ies))"
        return forms
    return re.compile(r"\b" + r"\s+".join(one(w) for w in norm(term).split()) + r"\b")


def focus():
    try:
        return set(json.loads((ROOT / "data/focus_species.json").read_text()))
    except (OSError, json.JSONDecodeError):
        return set()


def stats(term, names, texts, foc):
    r = term_re(term)
    hits = [(sid, en) for sid, en in names if r.search(en)]
    n_texts = sum(1 for t in texts if r.search(t))
    # regular species first, then names where the term is the last word ("Barred Hawk" before "Hawk-Eagle"),
    # then focus species of the route
    last = re.compile(r"(?:" + r.pattern + r")$")
    ex = [sid for sid, en in sorted(hits, key=lambda h: (h[0] in RARE, not last.search(h[1]), h[0] not in foc))][:3]
    return len(hits), n_texts, ex


def fill(path, names, texts):
    foc = focus()
    lines = Path(path).read_text().splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^- en: (.+?)\s*$", line)
        if not m:
            out.append(line)
            i += 1
            continue
        term = m.group(1).strip().strip("'\"")
        block, keep_empty = [line], False
        i += 1
        while i < len(lines) and lines[i].startswith("  "):
            keep_empty |= lines[i].strip() == "examples: []"
            if not re.match(r"^  (freq|examples):", lines[i]):
                block.append(lines[i])
            i += 1
        n, t, ex = stats(term, names, texts, foc)
        block.append(f"  freq: {n + t}")
        if keep_empty:  # `examples: []` in the file = the names use the word in another sense; keep it empty
            block.append("  examples: []")
        elif ex:
            block.append(f"  examples: [{', '.join(ex)}]")
        out.extend(block)
    Path(path).write_text("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--top", type=int, default=400)
    ap.add_argument("--intro-only", action="store_true", help="count only Wikipedia intros, not sections")
    ap.add_argument("--word", nargs="*")
    ap.add_argument("--fill")
    a = ap.parse_args()

    names, texts, intros = load()
    if a.intro_only:
        texts = intros
    if a.fill:
        fill(a.fill, names, texts)
        return
    if a.word:
        foc = focus()
        for w in a.word:
            n, t, ex = stats(w, names, texts, foc)
            print(f"{w}\t{n}\t{t}\t{n + t}\t{' '.join(ex)}")
        return

    in_names, in_texts = Counter(), Counter()
    for _, en in names:
        in_names.update(set(TOKEN.findall(en)))
    for t in texts:
        in_texts.update(set(TOKEN.findall(t)))
    total = Counter({w: in_names[w] + in_texts[w] for w in set(in_names) | set(in_texts)
                     if w not in STOP and len(w) > 2})
    print(f"# {len(names)} names, {len(texts)} texts\n# word\tnames\ttexts\ttotal")
    for w, n in total.most_common(a.top):
        print(f"{w}\t{in_names[w]}\t{in_texts[w]}\t{n}")


if __name__ == "__main__":
    main()
