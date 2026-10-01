"""Fetch python/peps at a pinned commit and vendor the typing subset into data/raw.

The vendored copy is committed, so `build` works offline; `fetch` is only
needed to regenerate it (e.g. after bumping PEPS_COMMIT).
"""
import re
import shutil
import subprocess

from .config import CACHE_DIR, EXTRA_PEPS, PEPS_COMMIT, PEPS_REPO, RAW_DIR

TOPIC_RE = re.compile(r"^Topic:.*\bTyping\b", re.MULTILINE)


def _git(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True)


def ensure_checkout():
    if not (CACHE_DIR / ".git").exists():
        CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--filter=blob:none", PEPS_REPO, str(CACHE_DIR))
    _git("fetch", "--depth", "1", "origin", PEPS_COMMIT, cwd=CACHE_DIR)
    _git("checkout", "--quiet", PEPS_COMMIT, cwd=CACHE_DIR)


def select_corpus(peps_dir):
    """Return {pep_number: path} for the typing subset."""
    selected = {}
    for path in sorted(peps_dir.glob("pep-*.rst")):
        number = int(path.stem.split("-")[1])
        head = path.read_text(encoding="utf-8")[:3000]
        if TOPIC_RE.search(head) or number in EXTRA_PEPS:
            selected[number] = path
    return selected


def write_index(peps_dir):
    """Record number -> title for *every* PEP so references outside the corpus
    can become labelled stub nodes instead of dangling numbers."""
    titles = {}
    for path in sorted(peps_dir.glob("pep-*.rst")):
        m = re.search(r"^Title:\s*(.+)$", path.read_text(encoding="utf-8")[:2000], re.MULTILINE)
        if m:
            titles[int(path.stem.split("-")[1])] = m.group(1).strip()
    lines = [f"{n}\t{t}" for n, t in sorted(titles.items())]
    (RAW_DIR.parent / "pep_titles.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run():
    ensure_checkout()
    peps_dir = CACHE_DIR / "peps"
    corpus = select_corpus(peps_dir)
    if RAW_DIR.exists():
        shutil.rmtree(RAW_DIR)
    RAW_DIR.mkdir(parents=True)
    for path in corpus.values():
        shutil.copy2(path, RAW_DIR / path.name)
    write_index(peps_dir)
    (RAW_DIR.parent / "SOURCE.md").write_text(
        f"# Data source\n\n- Repository: {PEPS_REPO}\n- Commit: `{PEPS_COMMIT}`\n"
        f"- Selection: `Topic: Typing` header, plus {sorted(EXTRA_PEPS)} (see pepatlas/config.py)\n"
        f"- Files vendored: {len(corpus)}\n- License: PEPs are public domain / CC0-1.0-Universal\n"
        f"- `pep_titles.tsv`: number/title of every PEP, used to label out-of-corpus references\n",
        encoding="utf-8",
    )
    print(f"Vendored {len(corpus)} PEPs into {RAW_DIR}")
    return corpus
