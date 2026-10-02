"""The knowledge graph container: typed nodes, typed edges with provenance,
deterministic JSON serialization, and the few indexes the reasoner needs."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

SCHEMA_VERSION = 1

NODE_TYPES = {
    "PEP": "A Python Enhancement Proposal in (or referenced by) the typing corpus",
    "Person": "An author, sponsor or decision-maker (delegate) of PEPs",
    "Concept": "A typing construct or idea from the curated lexicon",
    "RejectedIdea": "An alternative a PEP considered and explicitly turned down",
    "Concern": "A recurring category of objection",
    "Decision": "The recorded outcome of a PEP, with its stated rationale",
    "PythonVersion": "A CPython release targeted by a PEP",
    "Venue": "Where a PEP was discussed (mailing list or forum)",
    "Tool": "A type checker or typing tool referenced by PEPs",
}

EDGE_TYPES = {
    "AUTHORED_BY": ("PEP", "Person", "Author header"),
    "SPONSORED_BY": ("PEP", "Person", "Sponsor header"),
    "DECIDED_BY": ("Decision", "Person", "BDFL-Delegate / PEP-Delegate header"),
    "HAS_DECISION": ("PEP", "Decision", "Status + Resolution header + decision sections"),
    "REQUIRES": ("PEP", "PEP", "Requires header"),
    "REPLACES": ("PEP", "PEP", "Replaces header"),
    "SUPERSEDED_BY": ("PEP", "PEP", "Superseded-By header"),
    "BUILDS_ON": ("PEP", "PEP", "Reference to an earlier accepted PEP from abstract/motivation/specification"),
    "CONTRASTS_WITH": ("PEP", "PEP", "Reference made inside a rejected-alternatives section"),
    "REFERENCES": ("PEP", "PEP", "Any other :pep: / 'PEP N' reference"),
    "INTRODUCES": ("PEP", "Concept", "First accepted PEP focused on the concept"),
    "EXTENDS": ("PEP", "Concept", "Later accepted PEP focused on an already-introduced concept"),
    "PROPOSES": ("PEP", "Concept", "Non-accepted (draft/rejected/withdrawn) PEP focused on the concept"),
    "MENTIONS": ("PEP", "Concept", "Concept discussed but not the PEP's focus"),
    "CONSIDERED": ("PEP", "RejectedIdea", "Sub-section of a rejected/alternatives section"),
    "ABOUT": ("RejectedIdea", "Concept", "Lexicon match in the idea's heading/text"),
    "RAISES": ("RejectedIdea|PEP", "Concern", "Concern cue in a rejection reason or compat/open-issues section"),
    "REVISITED_BY": ("RejectedIdea", "PEP", "Derived: a later accepted PEP that cites the rejecting PEP and works on the same concept with similar wording"),
    "TARGETS": ("PEP", "PythonVersion", "Python-Version header"),
    "DISCUSSED_AT": ("PEP", "Venue", "Discussions-To / Post-History headers"),
    "IMPLEMENTED_IN": ("PEP", "Tool", "Tool named in a reference-implementation section"),
    "MENTIONS_TOOL": ("PEP", "Tool", "Tool named elsewhere"),
}


class KnowledgeGraph:
    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self.meta: dict = {}
        self._out = defaultdict(list)
        self._in = defaultdict(list)

    # ----------------------------------------------------------- mutation
    def add_node(self, node_id: str, type_: str, **attrs) -> str:
        assert type_ in NODE_TYPES, type_
        if node_id in self.nodes:
            self.nodes[node_id].update({k: v for k, v in attrs.items() if v not in (None, "", [], {})})
        else:
            self.nodes[node_id] = {"id": node_id, "type": type_, **attrs}
        return node_id

    def add_edge(self, src: str, dst: str, type_: str, *, confidence: float, source: str,
                 section: str | None = None, evidence: str | None = None, **attrs):
        assert type_ in EDGE_TYPES, type_
        assert src in self.nodes and dst in self.nodes, (src, dst)
        e = {"src": src, "dst": dst, "type": type_, "confidence": round(confidence, 3), "source": source}
        if section:
            e["section"] = section
        if evidence:
            e["evidence"] = evidence[:400]
        e.update(attrs)
        self.edges.append(e)
        self._out[src].append(e)
        self._in[dst].append(e)
        return e

    def remove_edges(self, predicate):
        self.edges = [e for e in self.edges if not predicate(e)]
        self._reindex()

    # ----------------------------------------------------------- queries
    def out(self, node_id: str, type_: str | None = None) -> list[dict]:
        return [e for e in self._out.get(node_id, []) if type_ is None or e["type"] == type_]

    def into(self, node_id: str, type_: str | None = None) -> list[dict]:
        return [e for e in self._in.get(node_id, []) if type_ is None or e["type"] == type_]

    def of_type(self, type_: str) -> list[dict]:
        return [n for n in self.nodes.values() if n["type"] == type_]

    def get(self, node_id: str) -> dict | None:
        return self.nodes.get(node_id)

    def label(self, node_id: str) -> str:
        n = self.nodes.get(node_id, {})
        if n.get("type") == "PEP":
            return f"PEP {n['number']}: {n.get('title', '?')}"
        return n.get("label") or n.get("name") or n.get("title") or node_id

    # ----------------------------------------------------------- io
    def _reindex(self):
        self._out, self._in = defaultdict(list), defaultdict(list)
        for e in self.edges:
            self._out[e["src"]].append(e)
            self._in[e["dst"]].append(e)

    def to_json(self) -> dict:
        def node_key(n):
            return (n["type"], n["id"])
        type_counts = defaultdict(int)
        for n in self.nodes.values():
            type_counts[n["type"]] += 1
        edge_counts = defaultdict(int)
        for e in self.edges:
            edge_counts[e["type"]] += 1
        return {
            "schema_version": SCHEMA_VERSION,
            "meta": self.meta,
            "stats": {"nodes": dict(sorted(type_counts.items())), "edges": dict(sorted(edge_counts.items()))},
            "schema": {
                "node_types": NODE_TYPES,
                "edge_types": {k: {"from": a, "to": b, "rule": r} for k, (a, b, r) in EDGE_TYPES.items()},
            },
            "nodes": sorted(self.nodes.values(), key=node_key),
            "edges": sorted(self.edges, key=lambda e: (e["type"], e["src"], e["dst"], e.get("section", ""))),
        }

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    @classmethod
    def load(cls, path: Path) -> "KnowledgeGraph":
        data = json.loads(path.read_text(encoding="utf-8"))
        g = cls()
        g.meta = data.get("meta", {})
        g.nodes = {n["id"]: n for n in data["nodes"]}
        g.edges = data["edges"]
        g._reindex()
        return g
