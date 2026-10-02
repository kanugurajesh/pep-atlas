"""Extraction rules checked against facts about typing history that are known
independently of this code."""
import json
import os
import subprocess
import sys

from pepatlas.config import ROOT
from pepatlas.extract import build_graph
from tests.conftest import edge_types


def test_header_relations(graph):
    assert "SUPERSEDED_BY" in edge_types(graph, "pep:563", "pep:649")
    assert "REQUIRES" in edge_types(graph, "pep:749", "pep:649")
    authors = {graph.nodes[e["dst"]]["name"] for e in graph.out("pep:484", "AUTHORED_BY")}
    assert "Guido van Rossum" in authors


def test_concept_introductions_follow_history(graph):
    def introducer(concept):
        return {graph.nodes[e["src"]]["number"] for e in graph.into(f"concept:{concept}", "INTRODUCES")}
    assert introducer("protocols") == {544}
    assert introducer("typeddict") == {589}
    assert introducer("union_operator") == {604}
    assert introducer("builtin_generics") == {585}
    assert introducer("type_param_syntax") == {695}
    assert introducer("typevar") == {484}
    assert introducer("function_annotations") == {3107}


def test_later_accepted_peps_extend_not_introduce(graph):
    assert "EXTENDS" in edge_types(graph, "pep:655", "concept:typeddict")
    assert "EXTENDS" in edge_types(graph, "pep:604", "concept:union")


def test_failed_and_draft_peps_only_propose(graph):
    assert "PROPOSES" in edge_types(graph, "pep:677", "concept:callable_syntax")
    assert "PROPOSES" in edge_types(graph, "pep:645", "concept:optional_shorthand")
    assert not graph.into("concept:inline_typeddict", "INTRODUCES")     # PEP 764 is still a draft


def test_references_are_typed_by_section(graph):
    assert "BUILDS_ON" in edge_types(graph, "pep:742", "pep:647")
    # a later PEP never "builds on" an earlier one in the wrong direction
    for e in graph.edges:
        if e["type"] == "BUILDS_ON":
            assert graph.nodes[e["dst"]]["created"] < graph.nodes[e["src"]]["created"]


def test_rejected_ideas_and_reasons(graph):
    ideas = {n["title"]: n for n in graph.of_type("RejectedIdea") if n["pep"] == 484}
    assert "Which brackets for generic type parameters?" in ideas
    nongoal = next(n for n in graph.of_type("RejectedIdea") if n["pep"] == 484 and n["kind"] == "non_goal")
    assert "mandatory" in nongoal["reason"]


def test_decisions_capture_rationale(graph):
    assert "T|None" in graph.nodes["decision:645"]["rationale"].replace(" ", "")
    assert "Steering Council" in graph.nodes["decision:712"]["rationale"]
    assert "new syntax" in graph.nodes["decision:637"]["rationale"]


def test_revisits_point_forward_in_time(graph):
    found = False
    for e in graph.edges:
        if e["type"] == "REVISITED_BY":
            idea, later = graph.nodes[e["src"]], graph.nodes[e["dst"]]
            assert later["year"] >= idea["year"] and later["outcome"] == "accepted"
            found |= (idea["pep"] == 647 and later["number"] == 742)
    assert found, "PEP 647's rejected strict narrowing should be revisited by PEP 742 (TypeIs)"


def test_every_edge_has_provenance(graph):
    for e in graph.edges:
        assert e["source"] and 0 < e["confidence"] <= 1


def test_build_is_deterministic(graph):
    again = build_graph()
    assert json.dumps(again.to_json(), sort_keys=True) == json.dumps(graph.to_json(), sort_keys=True)


def test_build_is_deterministic_across_hash_seeds():
    # Set iteration order changes with PYTHONHASHSEED, so a same-process rebuild
    # cannot catch an ordering that depends on it (it once reordered PEP 484's focus list).
    code = "import json; from pepatlas.extract import build_graph; print(json.dumps(build_graph().to_json()))"
    outs = [subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=ROOT,
                           env={**os.environ, "PYTHONHASHSEED": seed}).stdout for seed in ("0", "3")]
    assert outs[0] == outs[1]
