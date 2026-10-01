from pepatlas import lexicon as lx
from pepatlas.config import RAW_DIR
from pepatlas.extract import is_generic_heading, split_people
from pepatlas.parse import load, parse_headers, plain


def test_headers_with_continuation_lines():
    headers, body = parse_headers(["PEP: 1", "Author: A <a@x>,", "  B <b@x>", "Status: Final", "", "body"])
    assert headers["Author"] == "A <a@x>, B <b@x>"
    assert body == 5


def test_section_tree_of_pep_484():
    doc = load(RAW_DIR / "pep-0484.rst")
    assert doc.headers["Title"] == "Type Hints"
    top = [s.title for s in doc.root.children]
    assert top[0] == "Abstract" and "Rejected Alternatives" in top
    rejected = doc.top_level("Rejected Alternatives")
    assert "Which brackets for generic type parameters?" in [c.title for c in rejected.children]
    # nested sections know their path
    nongoals = next(s for s in doc.sections() if s.title == "Non-goals")
    assert nongoals.path == ["Rationale and Goals", "Non-goals"]


def test_every_corpus_file_parses():
    for path in sorted(RAW_DIR.glob("pep-*.rst")):
        doc = load(path)
        assert doc.sections(), path.name
        assert doc.headers.get("Status"), path.name


def test_plain_strips_roles_and_literals():
    assert plain(":pep:`484` adds ``Callable``") == "484 adds Callable"


def test_split_people_keeps_commas_inside_brackets():
    assert split_people("Guido van Rossum <guido@python.org>, Jukka <j@x>") == [
        ("Guido van Rossum", "guido@python.org"), ("Jukka", "j@x")]


def test_section_kinds():
    assert lx.section_kind(["Rejected Ideas", "Using brackets"]) == "rejected"
    assert lx.section_kind(["Rejection Notice"]) == "decision"
    assert lx.section_kind(["Forward references"]) != "meta"      # not the "References" footnote section
    assert lx.section_kind(["Abstract generic types"]) != "abstract"
    assert lx.section_kind(["Rationale and Goals", "Non-goals"]) == "rejected"


def test_generic_headings():
    assert is_generic_heading("Rejected/Postponed Proposals")
    assert not is_generic_heading("Why not use namedtuple?")
