"""Golden cases: new inputs (written for this test, not taken from PEPs) and the
verdicts a typing expert would expect."""
import pytest

CASES = [
    ("Add a shorthand syntax for callable types like (int, str) -> bool instead of Callable[[int, str], bool]",
     "previously_rejected", 677),
    ("Allow T? as a shorthand for Optional[T] in annotations", "previously_rejected", 645),
    ("Write a TypedDict inline in an annotation without declaring a class first", "in_progress", 764),
    ("A decorator to mark that a method overrides a method in the base class, so type checkers catch typos",
     "already_exists", 698),
]


@pytest.mark.parametrize("text,label,pep", CASES)
def test_verdicts(engine, text, label, pep):
    r = engine.assess(text)
    assert r["verdict"]["label"] == label, r["verdict"]
    assert r["closest_peps"][0]["pep"] == pep


def test_runtime_enforcement_warns_about_non_goal(engine):
    r = engine.assess("Python should enforce type hints at runtime and raise TypeError on wrong argument types")
    assert any("non-goal of PEP 484" in w for w in r["verdict"]["warnings"])
    titles = [i["idea"] for i in r["rejected_ideas"]]
    assert "Runtime enforcement" in titles          # PEP 698's rejected alternative


def test_unknown_territory_is_not_overclaimed(engine):
    r = engine.assess("Make the garbage collector generational with three generations")
    assert r["verdict"]["label"] == "outside_known_territory"


def test_output_is_grounded(engine, graph):
    r = engine.assess("Allow T? as a shorthand for Optional[T]")
    for p in r["closest_peps"]:
        assert f"pep:{p['pep']}" in graph.nodes
    for i in r["rejected_ideas"]:
        assert any(n["title"] == i["idea"] and n["pep"] == i["pep"] for n in graph.of_type("RejectedIdea"))


def test_reading_list_is_in_chronological_order(engine, graph):
    r = engine.assess("A new special form for typing keyword arguments with a TypedDict")
    years = [graph.nodes[f"pep:{p['pep']}"]["created"] for p in r["read_first"]
             if p["why"].startswith("foundation")]
    assert years == sorted(years)


def test_explain_follows_supersession(engine):
    r = engine.explain("Why wasn't from __future__ import annotations made the default?")
    peps = [t["pep"] for t in r["timeline"]]
    assert peps.index(563) < peps.index(649) < peps.index(749)


def test_rejected_ideas_are_on_topic(engine):
    r = engine.assess("Allow T? as a shorthand for Optional[T] in annotations")
    peps = {i["pep"] for i in r["rejected_ideas"]}
    # PEP 675's "Why not use tool X?" (SQL tooling) once matched the `X?` concept,
    # and PEP 727's slice shorthand / PEP 544's intersections got in on shared words.
    assert not peps & {675, 727, 544}, r["rejected_ideas"]


def test_objection_quotes_come_from_listed_sources(engine):
    for text in ("Allow T? as a shorthand for Optional[T] in annotations",
                 "Python should enforce type hints at runtime and raise TypeError on wrong argument types"):
        r = engine.assess(text)
        ideas = {f"PEP {i['pep']} (rejected idea: {i['idea']})" for i in r["rejected_ideas"]}
        area = {i["pep"] for i in r["area_track_record"]["peps"]}
        for o in r["objections_to_prepare_for"]:
            for ex in o["examples"]:
                assert ex["source"] in ideas or int(ex["source"].split()[1]) in area, ex


def test_wording_alone_claims_no_precedent(engine):
    # No typing concept: shared words ("dictionary", "keys") once gave "already exists -> TypedDict".
    r = engine.assess("Speed up dictionary lookups by caching hash values of string keys inside the interpreter.")
    assert r["verdict"]["label"] == "outside_known_territory"
    assert r["verdict"]["basis"]["wording_only"]


def test_named_pep_is_an_anchor_without_concepts(engine):
    # No lexicon concept in the text, but the user names the PEP: that is not "wording only",
    # and the report must not say no typing concept was recognised.
    r = engine.assess("I want to revive PEP 677 with a few changes")
    assert r["verdict"]["label"] == "extends_existing_area", r["verdict"]
    assert "PEP 677" in r["verdict"]["summary"]
    assert r["closest_peps"][0]["pep"] == 677
