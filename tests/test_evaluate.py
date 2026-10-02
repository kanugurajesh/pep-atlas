"""The verdict benchmark's case file is well-formed and refers to real PEPs."""
from pepatlas.evaluate import LABELS, load_verdict_cases


def test_verdict_cases_are_valid(graph):
    cases = load_verdict_cases()
    assert len({c["id"] for c in cases}) == len(cases)
    for c in cases:
        assert c["expected_label"] in LABELS, c["id"]
        assert set(c.get("also_acceptable", [])) <= set(LABELS), c["id"]
        assert c["text"] and c["source"], c["id"]
        if c.get("expected_pep"):
            assert f"pep:{c['expected_pep']}" in graph.nodes, c["id"]


def test_verdict_cases_cover_every_label():
    assert {c["expected_label"] for c in load_verdict_cases()} == set(LABELS)


def test_verdict_cases_do_not_name_peps():
    # Inputs must not hand the answer over.
    for c in load_verdict_cases():
        assert "PEP" not in c["text"], c["id"]
