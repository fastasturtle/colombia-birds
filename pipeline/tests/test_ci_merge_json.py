"""Tests for ci_merge_json.py (3-way merge of species JSON in ci_commit.sh) and ci_commit.sh end to end.

Run: `cd pipeline && uv run python tests/test_ci_merge_json.py` (plain asserts, no pytest needed;
the test_* functions also work under pytest). The end-to-end test needs git and bash.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent
sys.path.insert(0, str(PIPELINE))
import ci_merge_json as m  # noqa: E402

SPECIES = {
    "id": "dacnis-egregia",
    "sci": "Dacnis egregia",
    "photos": [],
    "links": {"wikipedia": {"en": None}},
    "ids": {"wikidata": None},
}


def test_species_both_sides_kept():
    base = SPECIES
    run = {**base, "photos": [{"key_base": "photos/dacnis-egregia/1"}]}             # heavy queue: upload
    remote = {**base, "links": {"wikipedia": {"en": "Scarlet-breasted dacnis"}},     # light queue: build
              "ids": {"wikidata": "Q31874408"}}
    out = m.merge_dict(base, remote, run)
    assert out["photos"] == run["photos"]
    assert out["links"] == remote["links"] and out["ids"] == remote["ids"]


def test_species_same_key_run_wins_and_removed_key():
    base = {**SPECIES, "texts": {"en": "old"}}
    run = {k: v for k, v in base.items() if k != "texts"} | {"photos": [1]}
    remote = {**base, "photos": [2], "sounds": [3]}
    out = m.merge_dict(base, remote, run)
    assert out["photos"] == [1]          # changed on both sides: this run's value
    assert "texts" not in out            # removed by this run
    assert out["sounds"] == [3]          # added upstream


def test_species_new_in_run():
    assert m.merge("data/species/x.json", None, None, {"a": 1}) == {"a": 1}
    # added on both sides (e.g. a remap built by both runs): run's keys over the remote file
    assert m.merge("data/species/x.json", None, {"a": 0, "b": 2}, {"a": 1}) == {"a": 1, "b": 2}


def _entry(i, **kw):
    return {"id": i, "photo": None, "ru": None, **kw}


def test_index_photo_vs_ru():
    base = [_entry("a"), _entry("b"), _entry("c")]
    run = [_entry("a"), _entry("b", photo="photos/b/1-thumb.jpg"), _entry("c")]       # upload
    remote = [_entry("a", ru="Имя"), _entry("b", ru="Кваква"), _entry("c")]           # build
    out = m.merge_index(base, remote, run)
    assert [e["id"] for e in out] == ["a", "b", "c"]
    assert out[0] == _entry("a", ru="Имя")
    assert out[1] == _entry("b", photo="photos/b/1-thumb.jpg", ru="Кваква")


def test_index_membership_changes():
    base = [_entry("a"), _entry("b"), _entry("c")]
    # this run (build) renamed b -> b2 and reordered; upstream set a photo on c and added d after c
    run = [_entry("c"), _entry("a"), _entry("b2")]
    remote = [_entry("a"), _entry("b"), _entry("c", photo="p"), _entry("d")]
    out = m.merge_index(base, remote, run)
    assert [e["id"] for e in out] == ["c", "d", "a", "b2"]
    assert out[0]["photo"] == "p"
    # upstream deleted a (untouched by the run): stays deleted
    out = m.merge_index(base, [_entry("b"), _entry("c")], [_entry("a"), _entry("b"), _entry("c", ru="x")])
    assert [e["id"] for e in out] == ["b", "c"] and out[1]["ru"] == "x"


def _git(cwd, *args, **kw):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, **kw).stdout.strip()


def _write(root: Path, rel: str, obj) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(m.dumps(obj))


def test_ci_commit_end_to_end():
    """Two runs from the same base: upstream pushes new links/ru, this run adds photos; both survive."""
    if not shutil.which("git") or not shutil.which("bash"):
        return
    tmp = Path(tempfile.mkdtemp())
    try:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t"}
        origin, run_wt, other = tmp / "origin.git", tmp / "run", tmp / "other"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(origin), str(run_wt)], check=True, capture_output=True)
        (run_wt / "pipeline").mkdir()
        shutil.copy(PIPELINE / "ci_commit.sh", run_wt / "pipeline")
        shutil.copy(PIPELINE / "ci_merge_json.py", run_wt / "pipeline")
        _write(run_wt, "data/species/b.json", SPECIES)
        _write(run_wt, "data/species/gone.json", SPECIES)
        _write(run_wt, "data/species_index.json", [_entry("a"), _entry("b")])
        _write(run_wt, "data/other.json", {"v": 0})
        _git(run_wt, "add", "-A", env=env)
        _git(run_wt, "commit", "-q", "-m", "base", env=env)
        _git(run_wt, "push", "-q", "origin", "HEAD:main", env=env)
        base = _git(run_wt, "rev-parse", "HEAD")

        # the other queue: build writes links + ru, pushes first
        subprocess.run(["git", "clone", "-q", str(origin), str(other)], check=True, capture_output=True)
        _write(other, "data/species/b.json", {**SPECIES, "links": {"wikipedia": {"en": "B"}}})
        _write(other, "data/species_index.json", [_entry("a"), _entry("b", ru="Б")])
        _write(other, "data/other.json", {"v": 1})
        _git(other, "commit", "-q", "-am", "upstream", env=env)
        _git(other, "push", "-q", "origin", "HEAD:main", env=env)

        # this run: upload writes photos, a new species file, deletes one, touches other.json
        _write(run_wt, "data/species/b.json", {**SPECIES, "photos": [{"k": 1}]})
        _write(run_wt, "data/species/new.json", {"id": "new"})
        (run_wt / "data/species/gone.json").unlink()
        _write(run_wt, "data/species_index.json", [_entry("a"), _entry("b", photo="t.jpg")])
        _write(run_wt, "data/other.json", {"v": 2})
        r = subprocess.run(["bash", "pipeline/ci_commit.sh", "data: test"], cwd=run_wt, capture_output=True,
                           text=True, env={**env, "BASE_SHA": base, "BRANCH": "main"})
        assert r.returncode == 0, r.stdout + r.stderr

        def shown(path):
            return json.loads(_git(run_wt, "show", f"origin/main:{path}"))

        _git(run_wt, "fetch", "-q", "origin")
        b = shown("data/species/b.json")
        assert b["photos"] == [{"k": 1}] and b["links"] == {"wikipedia": {"en": "B"}}
        assert shown("data/species_index.json") == [_entry("a"), _entry("b", photo="t.jpg", ru="Б")]
        assert shown("data/species/new.json") == {"id": "new"}
        assert shown("data/other.json") == {"v": 2}  # other paths: this run's whole file, as before
        assert "data/species/gone.json" not in _git(run_wt, "ls-tree", "-r", "--name-only", "origin/main")
        assert _git(run_wt, "rev-parse", "HEAD") == base  # checkout untouched
        assert json.loads((run_wt / "data/species/b.json").read_text())["links"] == SPECIES["links"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok {name}")
