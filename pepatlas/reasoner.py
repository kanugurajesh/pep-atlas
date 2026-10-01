"""Reasoning over the knowledge graph for a new, unseen input.

The reasoner reads only the serialized knowledge state (graph.json), never the
raw PEP files. Everything it says is therefore traceable to a node or an edge,
and every edge carries the PEP and section it came from.

Pipeline for `assess`:
  1. profile   map the free text onto the graph's vocabulary (concepts, intents, PEP mentions)
  2. anchor    score PEPs and rejected ideas: graph relations first, wording second
  3. expand    walk the graph from the anchors (supersession, foundations, revisits, people)
  4. decide    produce a verdict with the evidence that triggered it
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import lexicon as lx
from .graph import KnowledgeGraph
from .textindex import TfidfIndex

# How strongly a PEP->Concept relation ties the PEP to the concept.
RELATION_STRENGTH = {"INTRODUCES": 1.0, "PROPOSES": 1.0, "EXTENDS": 0.8}
MENTION_STRENGTH = 0.3

# Score blending. The weights were set by hand and checked against the holdout
# evaluation (eval/results.md); they are deliberately few and round.
W_CONCEPT, W_TEXT = 0.55, 0.45
TEXT_SATURATION = 0.40          # cosine at which wording similarity counts as "full"
IDEA_TEXT_SATURATION = 0.30
EXPLICIT_MENTION_BOOST = 0.25

STRONG_MATCH = 0.62             # PEP score at which we claim "this has been proposed"
STRONG_TEXT = 0.22              # ...and wording must also overlap at least this much,
STRONG_CONCEPT = 0.80           # ...or the concepts must match almost completely
IDEA_MATCH = 0.55
NON_GOAL_MATCH = 0.35
PROPAGATION = 0.25              # share of a seed PEP's score passed to the PEPs it builds on
MIN_EVIDENCE = 0.6              # concept weight needed for a full concept score: one broad concept
                                # (e.g. runtime annotations, specificity ~0.26) earns at most ~40%


@dataclass
class Profile:
    text: str
    concepts: dict[str, list[str]]
    intents: list[str]
    pep_mentions: list[int]
    weights: dict[str, float] = field(default_factory=dict)


class Engine:
    def __init__(self, graph: KnowledgeGraph):
        self.g = graph
        self.peps = {n["id"]: n for n in graph.of_type("PEP") if n.get("in_corpus")}
        self.ideas = {n["id"]: n for n in graph.of_type("RejectedIdea")}
        self.w_concept, self.w_text = W_CONCEPT, W_TEXT
        self.pep_index = TfidfIndex({p: self._pep_doc(n) for p, n in self.peps.items()})
        self.idea_index = TfidfIndex({i: self._idea_doc(n) for i, n in self.ideas.items()})
        # concept -> {pep_id: strength}
        self.concept_peps: dict[str, dict[str, float]] = defaultdict(dict)
        for e in graph.edges:
            if e["src"] in self.peps and e["dst"].startswith("concept:"):
                if e["type"] in RELATION_STRENGTH:
                    s = RELATION_STRENGTH[e["type"]]
                elif e["type"] == "MENTIONS":
                    s = MENTION_STRENGTH * min(1.0, 2 * e.get("weight", 0))
                else:
                    continue
                self.concept_peps[e["dst"][8:]][e["src"]] = s
        n_peps = len(self.peps)
        # Specificity: a concept that many PEPs focus on (TypeVar) says less
        # about a proposal than one only two PEPs focus on (TypeIs).
        self.specificity = {}
        for c in lx.CONCEPT_BY_ID:
            focus = sum(1 for s in self.concept_peps.get(c, {}).values() if s >= 0.8)
            mentions = len(self.concept_peps.get(c, {}))
            self.specificity[c] = 1.0 / (1.0 + math.log(1 + focus + 0.25 * mentions)) if n_peps else 1.0

    @staticmethod
    def _pep_doc(n: dict) -> str:
        return " ".join([n["title"]] * 3 + [n.get("abstract", "")] + n.get("outline", []))

    @staticmethod
    def _idea_doc(n: dict) -> str:
        return " ".join([n["title"]] * 2 + [n.get("summary", ""), n.get("reason") or "", n.get("text", "")])

    # ------------------------------------------------------------------ profile
    def profile(self, text: str) -> Profile:
        concepts = lx.match_input(text)
        mentions = sorted({int(m) for m in re.findall(r"\bPEP[\s-]*0*(\d{1,4})\b", text, re.IGNORECASE)})
        # Concepts named by explicitly mentioned PEPs count too, at half weight.
        # Only concepts the graph has prior PEPs for can anchor retrieval; a
        # concept nobody has worked on yet says nothing about *which* prior
        # work is relevant (it is still reported, and it signals novelty).
        weights = {c: self.specificity.get(c, 0.5) for c in concepts if self.concept_peps.get(c)}
        for m in mentions:
            for c in self.g.nodes.get(f"pep:{m}", {}).get("focus_concepts", []):
                weights.setdefault(c, 0.5 * self.specificity.get(c, 0.5))
        return Profile(text, concepts, lx.detect_intents(text), mentions, weights)

    # ------------------------------------------------------------------ anchor
    def score_peps(self, prof: Profile, k: int = 10, exclude: set[str] = frozenset()) -> list[dict]:
        total_w = max(sum(prof.weights.values()), MIN_EVIDENCE)
        qvec = self.pep_index.query_vec(prof.text)
        out = []
        for p, n in self.peps.items():
            if p in exclude:
                continue
            via = []
            concept = 0.0
            for c, w in prof.weights.items():
                s = self.concept_peps.get(c, {}).get(p, 0.0)
                if s:
                    concept += w * s
                    rel = next((e["type"] for e in self.g.out(p) if e["dst"] == f"concept:{c}"), "MENTIONS")
                    via.append((c, rel))
            concept /= total_w
            cos = self.pep_index.similarity(qvec, p)
            text = min(1.0, cos / TEXT_SATURATION)
            score = self.w_concept * concept + self.w_text * text if prof.weights else text
            if n["number"] in prof.pep_mentions:
                score += EXPLICIT_MENTION_BOOST
            if score <= 0.05:
                continue
            out.append({"id": p, "score": round(score, 3), "concept_score": round(concept, 3),
                        "text_cosine": round(cos, 3), "via": via,
                        "shared_terms": self.pep_index.shared_terms(prof.text, p, 5)})
        out.sort(key=lambda r: (-r["score"], r["id"]))
        return out[:k]

    def related_peps(self, prof: Profile, k: int = 10, exclude: set[str] = frozenset(),
                     seeds: int = 5, spread: float = PROPAGATION) -> list[dict]:
        """Direct matches plus what they stand on: each of the top `seeds`
        PEPs passes a share of its score to the PEPs it BUILDS_ON / REQUIRES /
        CONTRASTS_WITH. A proposal similar to PEP X will be judged against what
        X was judged against, even when the proposal's wording never names it."""
        base = self.score_peps(prof, k=len(self.peps), exclude=exclude)
        scores = {r["id"]: dict(r, propagated=0.0) for r in base}
        for r in base[:seeds]:
            for e in self.g.out(r["id"]):
                if e["type"] in ("BUILDS_ON", "REQUIRES", "CONTRASTS_WITH", "REPLACES") and e["dst"] in self.peps                         and e["dst"] not in exclude:
                    t = scores.setdefault(e["dst"], {"id": e["dst"], "score": 0.0, "via": [], "propagated": 0.0,
                                                     "concept_score": 0.0, "text_cosine": 0.0, "shared_terms": []})
                    t["propagated"] += spread * r["score"]
        for t in scores.values():
            t["score"] = round(t["score"] + t["propagated"], 3)
        out = sorted(scores.values(), key=lambda r: (-r["score"], r["id"]))
        return out[:k]

    def score_ideas(self, prof: Profile, k: int = 6) -> list[dict]:
        total_w = max(sum(prof.weights.values()), MIN_EVIDENCE)
        qvec = self.idea_index.query_vec(prof.text)
        out = []
        for i, n in self.ideas.items():
            about = {e["dst"][8:]: e.get("weight", 1) for e in self.g.out(i, "ABOUT")}
            # ABOUT weight >= 4 means the concept is in the idea's own heading.
            concept = sum(w * min(1.0, about[c] / 4) for c, w in prof.weights.items() if c in about) / total_w
            cos = self.idea_index.similarity(qvec, i)
            text = min(1.0, cos / IDEA_TEXT_SATURATION)
            score = 0.45 * concept + 0.55 * text if prof.weights else text
            if score < 0.2:
                continue
            out.append({"id": i, "score": round(score, 3), "text_cosine": round(cos, 3),
                        "shared_concepts": sorted(set(prof.weights) & set(about))})
        out.sort(key=lambda r: (-r["score"], r["id"]))
        return out[:k]

    # ------------------------------------------------------------------ helpers
    def current_version(self, pep_id: str) -> list[str]:
        """Follow SUPERSEDED_BY to the PEPs that are in force now."""
        nxt = [e["dst"] for e in self.g.out(pep_id, "SUPERSEDED_BY")]
        nxt += [e["src"] for e in self.g.into(pep_id, "REPLACES") if e["src"] not in nxt]
        return nxt

    def _successors(self, pep_id: str) -> list[str]:
        out, stack = [], [pep_id]
        while stack:
            for nxt in self.current_version(stack.pop()):
                if nxt not in out and nxt in self.peps:
                    out.append(nxt)
                    stack.append(nxt)
        return out

    def foundations(self, seeds: list[str], limit: int = 5, max_depth: int = 2) -> list[dict]:
        """Accepted PEPs the seeds build on (up to two hops), oldest first, so
        they read as a curriculum. BUILDS_ON only points backwards in time, so
        sorting by creation date is a valid topological order. Direct
        foundations, and those shared by several seeds, are preferred; deeper
        hops drift away from the topic quickly."""
        best: dict[str, tuple[int, str]] = {}         # foundation -> (depth, path label)
        reach: dict[str, set[str]] = defaultdict(set)
        for seed in seeds:
            frontier = [(seed, 0, f"PEP {self.peps[seed]['number']}")]
            while frontier:
                node, depth, path = frontier.pop(0)
                if depth == max_depth:
                    continue
                for e in self.g.out(node):
                    d = e["dst"]
                    if e["type"] not in ("BUILDS_ON", "REQUIRES") or d not in self.peps or d in seeds:
                        continue
                    reach[d].add(seed)
                    if d not in best or depth + 1 < best[d][0]:
                        best[d] = (depth + 1, path)
                        frontier.append((d, depth + 1, f"PEP {self.peps[d]['number']} → {path}"))
        ranked = sorted(best, key=lambda d: (best[d][0], -len(reach[d]), d))[:limit]
        ranked.sort(key=lambda d: (self.peps[d]["created"] or "", d))
        return [{"id": d, "depth": best[d][0], "path": best[d][1]} for d in ranked]

    def people(self, scored: list[dict], limit: int = 5) -> list[dict]:
        acc: dict[str, dict] = {}
        for r in scored:
            p, s = r["id"], r["score"]
            roles = [(e["dst"], "author", 1.0) for e in self.g.out(p, "AUTHORED_BY")]
            roles += [(e["dst"], "sponsor", 0.6) for e in self.g.out(p, "SPONSORED_BY")]
            for d in self.g.out(p, "HAS_DECISION"):
                roles += [(e["dst"], "delegate", 0.8) for e in self.g.out(d["dst"], "DECIDED_BY")]
            year = self.peps[p].get("year") or 2000
            for person, role, w in roles:
                a = acc.setdefault(person, {"id": person, "score": 0.0, "roles": defaultdict(list), "last_year": 0})
                a["score"] += w * s
                a["roles"][role].append(self.peps[p]["number"])
                a["last_year"] = max(a["last_year"], year)
        latest = max((a["last_year"] for a in acc.values()), default=2026)
        for a in acc.values():
            a["score"] = round(a["score"] / (1 + (latest - a["last_year"]) / 6), 3)   # prefer people still active
            a["roles"] = {k: sorted(set(v)) for k, v in a["roles"].items()}
        return sorted(acc.values(), key=lambda a: (-a["score"], a["id"]))[:limit]

    def area_peps(self, concepts: list[str]) -> list[str]:
        out = set()
        for c in concepts:
            out |= {p for p, s in self.concept_peps.get(c, {}).items() if s >= 0.8}
        return sorted(out, key=lambda p: self.peps[p]["number"])

    def concerns(self, prof: Profile, ideas: list[dict], area: list[str]) -> list[dict]:
        """What reviewers are likely to push back on, ranked by historical weight."""
        weight: Counter = Counter()
        examples: dict[str, list[dict]] = defaultdict(list)

        def add(cid, w, edge, origin_label):
            weight[cid] += w
            if edge.get("evidence") and len(examples[cid]) < 2 and all(
                    x["source"] != origin_label for x in examples[cid]):
                examples[cid].append({"quote": edge["evidence"], "source": origin_label,
                                      "section": edge.get("section")})

        for r in ideas:
            node = self.ideas[r["id"]]
            for e in self.g.out(r["id"], "RAISES"):
                add(e["dst"][8:], 1.0 * r["score"], e, f"PEP {node['pep']} (rejected idea: {node['title']})")
        for p in area:
            n = self.peps[p]
            for e in self.g.out(p, "RAISES"):
                w = 0.6 if e.get("context") == "decision" else 0.25
                add(e["dst"][8:], w, e, f"PEP {n['number']} ({e.get('context')})")
        for intent in prof.intents:
            for cid in lx.INTENT_CONCERNS.get(intent, []):
                weight[cid] += 0.15
        total = sum(weight.values()) or 1.0
        out = []
        for cid, w in weight.most_common():
            if w / total < 0.04:
                continue
            out.append({"concern": cid, "label": lx.CONCERNS[cid][0], "weight": round(w / total, 3),
                        "examples": examples.get(cid, []),
                        "from_intent": [i for i in prof.intents if cid in lx.INTENT_CONCERNS.get(i, [])]})
        return out[:6]

    # ------------------------------------------------------------------ assess
    def assess(self, text: str, exclude: set[str] = frozenset()) -> dict:
        prof = self.profile(text)
        peps = self.score_peps(prof, k=8, exclude=exclude)
        ideas = self.score_ideas(prof)
        area = self.area_peps(list(prof.concepts))
        verdict = self.verdict(prof, peps, ideas)
        # A stated non-goal is a design stance, not just a passed-over option:
        # surface any the proposal runs into, whatever the verdict.
        verdict["warnings"] = [
            f"May conflict with a stated non-goal of PEP {self.ideas[r['id']]['pep']}: "
            f"\"{self.ideas[r['id']].get('reason') or self.ideas[r['id']].get('summary')}\""
            for r in ideas if self.ideas[r["id"]].get("kind") == "non_goal" and r["score"] >= NON_GOAL_MATCH]

        closest = []
        for r in peps[:5]:
            n = self.peps[r["id"]]
            why = [f"{'introduces' if rel == 'INTRODUCES' else rel.lower()} {lx.CONCEPT_BY_ID[c].label}"
                   for c, rel in r["via"] if rel != "MENTIONS"]
            why += [f"mentions {lx.CONCEPT_BY_ID[c].label}" for c, rel in r["via"] if rel == "MENTIONS"][:2]
            if r["shared_terms"]:
                why.append("shared wording: " + ", ".join(r["shared_terms"]))
            dec = self.decision(r["id"])
            closest.append({
                "pep": n["number"], "title": n["title"], "status": n["status"], "year": n["year"],
                "score": r["score"], "why": why, "url": n["url"],
                "superseded_by": [self.peps[x]["number"] for x in self.current_version(r["id"]) if x in self.peps],
                "decision": dec,
            })

        rejected = []
        for r in ideas[:5]:
            node = self.ideas[r["id"]]
            revisits = [{"pep": self.g.nodes[e["dst"]]["number"], "title": self.g.nodes[e["dst"]]["title"],
                         "status": self.g.nodes[e["dst"]]["status"], "confidence": e["confidence"]}
                        for e in self.g.out(r["id"], "REVISITED_BY")]
            rejected.append({
                "idea": node["title"], "pep": node["pep"], "section": node["section"], "year": node.get("year"),
                "score": r["score"], "summary": node.get("summary"), "reason": node.get("reason"),
                "concerns": [lx.CONCERNS[e["dst"][8:]][0] for e in self.g.out(r["id"], "RAISES")],
                "revisited_by": revisits,
            })

        seeds = [r["id"] for r in peps[:3] if self.peps[r["id"]]["outcome"] == "accepted"]
        reading = [{"pep": self.peps[f["id"]]["number"], "title": self.peps[f["id"]]["title"],
                    "why": "foundation of " + f["path"]}
                   for f in self.foundations(seeds)]
        for r in peps[:3]:
            n = self.peps[r["id"]]
            if all(x["pep"] != n["number"] for x in reading):
                reading.append({"pep": n["number"], "title": n["title"],
                                "why": "closest prior proposal" + (" (read why it failed)" if n["outcome"] == "failed" else "")})
        reading.sort(key=lambda x: (self.peps[f"pep:{x['pep']}"]["created"] or "", x["pep"]))

        people = [{"name": self.g.nodes[a["id"]]["name"], "roles": a["roles"], "last_active": a["last_year"]}
                  for a in self.people(peps[:6])]
        venue = self.venue(peps[:6])

        area_counts = Counter(self.peps[p]["outcome"] for p in area)
        return {
            "input": {
                "text": text,
                "concepts": [{"id": c, "label": lx.CONCEPT_BY_ID[c].label, "matched": m,
                              "specificity": round(self.specificity[c], 2)} for c, m in sorted(prof.concepts.items())],
                "intents": prof.intents,
                "pep_mentions": prof.pep_mentions,
            },
            "verdict": verdict,
            "closest_peps": closest,
            "rejected_ideas": rejected,
            "objections_to_prepare_for": self.concerns(prof, ideas[:5], area),
            "read_first": reading,
            "people_to_engage": people,
            "where_to_discuss": venue,
            "area_track_record": {
                "concepts": [lx.CONCEPT_BY_ID[c].label for c in sorted(prof.concepts)],
                "accepted": area_counts.get("accepted", 0), "failed": area_counts.get("failed", 0),
                "open": area_counts.get("open", 0),
                "peps": [{"pep": self.peps[p]["number"], "status": self.peps[p]["status"]} for p in area],
            },
        }

    def decision(self, pep_id: str) -> dict | None:
        for e in self.g.out(pep_id, "HAS_DECISION"):
            d = self.g.nodes[e["dst"]]
            if d.get("outcome_class") == "failed" or d.get("rationale"):
                return {"outcome": d["outcome"], "rationale": (d.get("rationale") or "")[:500] or None,
                        "resolution": d.get("resolution_url")}
        return None

    def venue(self, scored: list[dict]) -> dict | None:
        recent = sorted(scored, key=lambda r: -(self.peps[r["id"]]["year"] or 0))
        for r in recent:
            for e in self.g.out(r["id"], "DISCUSSED_AT"):
                return {"venue": self.g.nodes[e["dst"]]["label"],
                        "basis": f"most recent related PEP (PEP {self.peps[r['id']]['number']}, "
                                 f"{self.peps[r['id']]['year']}) was discussed there",
                        "example_thread": e.get("url")}
        return None

    def verdict(self, prof: Profile, peps: list[dict], ideas: list[dict]) -> dict:
        if not prof.concepts and (not peps or peps[0]["score"] < 0.3):
            return {"label": "outside_known_territory", "confidence": "low",
                    "summary": "The input does not map onto any typing concept in the knowledge base and no PEP "
                               "is a close textual match. Either it is genuinely new ground or it is outside the "
                               "typing corpus (this system only knows typing PEPs)."}
        top = peps[0] if peps else None
        tn = self.peps[top["id"]] if top else None
        if top and top["score"] >= STRONG_MATCH and (top["text_cosine"] >= STRONG_TEXT
                                                    or top["concept_score"] >= STRONG_CONCEPT):
            label = {"accepted": "already_exists", "failed": "previously_rejected", "open": "in_progress"}[tn["outcome"]]
            msg = {
                "already_exists": f"PEP {tn['number']} ({tn['title']}, {tn['status']}) covers this area and matches "
                                  f"the proposal closely. Check that it addresses your specific mechanism; if it does "
                                  f"not, it is the baseline your proposal extends.",
                "previously_rejected": f"PEP {tn['number']} ({tn['title']}) proposed this and was {tn['status'].lower()}. "
                                       "A new attempt has to answer the reasons recorded in its decision.",
                "in_progress": f"PEP {tn['number']} ({tn['title']}) is an open {tn['status'].lower()} on this topic; "
                               "contributing to it is likely more effective than a competing PEP.",
            }[label]
            sup = self.current_version(top["id"])
            if sup:
                msg += " It has since been superseded by " + ", ".join(
                    f"PEP {self.g.nodes[s]['number']}" for s in sup) + "."
            conf = "high" if top["score"] >= 0.75 else "medium"
            return {"label": label, "confidence": conf, "summary": msg,
                    "basis": {"pep": tn["number"], "score": top["score"], "text_cosine": top["text_cosine"]}}
        if ideas and ideas[0]["score"] >= IDEA_MATCH:
            i = self.ideas[ideas[0]["id"]]
            revisit = self.g.out(ideas[0]["id"], "REVISITED_BY")
            msg = (f"Something close to this was considered and rejected as an alternative in PEP {i['pep']} "
                   f"(\"{i['title']}\").")
            if revisit:
                msg += f" That ground was later revisited by PEP {self.g.nodes[revisit[0]['dst']]['number']}."
            return {"label": "previously_rejected_alternative", "confidence": "medium", "summary": msg,
                    "basis": {"idea": i["title"], "pep": i["pep"], "score": ideas[0]["score"]}}
        if prof.concepts:
            labels = ", ".join(lx.CONCEPT_BY_ID[c].label for c in sorted(prof.concepts))
            near = f" Nearest prior work: PEP {tn['number']} ({tn['title']})." if tn else ""
            return {"label": "extends_existing_area", "confidence": "medium",
                    "summary": f"No PEP matches closely enough to call it the same proposal, but it builds on established concepts "
                               f"({labels}).{near} Expect to be measured against the decisions made there.",
                    "basis": {"top_score": top["score"] if top else 0}}
        return {"label": "outside_known_territory", "confidence": "low",
                "summary": "Only weak textual overlap with known PEPs; no typing concept recognised.",
                "basis": {"top_score": top["score"] if top else 0}}

    # ------------------------------------------------------------------ explain
    def explain(self, text: str) -> dict:
        """'Why does X work this way?' A concept's lineage through PEPs, with
        the alternatives that were turned down at each step."""
        prof = self.profile(text)
        concepts = sorted(prof.weights, key=lambda c: -prof.weights[c])[:3]
        if not concepts:
            ranked = self.score_peps(prof, k=3)
            if ranked:
                concepts = self.g.nodes[ranked[0]["id"]].get("focus_concepts", [])[:2]
        # A concept's story continues through whatever superseded the PEPs
        # that introduced it: postponed evaluation (563) -> deferred evaluation
        # (649, 749). Pull in the successors' own new concepts.
        for c in list(concepts):
            for p, s in self.concept_peps.get(c, {}).items():
                if s < 0.8:
                    continue
                for succ in self._successors(p):
                    for e in self.g.out(succ, "INTRODUCES"):
                        if e["dst"][8:] not in concepts:
                            concepts.append(e["dst"][8:])
        timeline = []
        for c in concepts:
            for p, s in self.concept_peps.get(c, {}).items():
                if s < 0.8 and not prof.pep_mentions:
                    continue
                n = self.peps[p]
                rel = next(e["type"] for e in self.g.out(p) if e["dst"] == f"concept:{c}")
                if rel == "MENTIONS":
                    continue
                timeline.append({"date": n["created"], "pep": n["number"], "title": n["title"], "status": n["status"],
                                 "relation": rel, "concept": lx.CONCEPT_BY_ID[c].label,
                                 "superseded_by": [self.g.nodes[x]["number"] for x in self.current_version(p)],
                                 "decision": self.decision(p)})
        merged = {}
        for t in sorted(timeline, key=lambda t: (t["date"] or "", t["pep"])):
            if t["pep"] in merged:
                merged[t["pep"]]["concept"] += ", " + t["concept"]
            else:
                merged[t["pep"]] = t
        # Alternatives turned down along the way, most relevant to the question first.
        ideas = []
        qvec = self.idea_index.query_vec(text)
        for i, n in self.ideas.items():
            about = {e["dst"][8:] for e in self.g.out(i, "ABOUT")}
            if not about & set(concepts):
                continue
            ideas.append((self.idea_index.similarity(qvec, i), i, n))
        ideas.sort(key=lambda x: (-x[0], x[1]))
        return {
            "input": {"text": text, "concepts": [lx.CONCEPT_BY_ID[c].label for c in concepts]},
            "timeline": list(merged.values()),
            "turned_down": [{"idea": n["title"], "pep": n["pep"], "year": n.get("year"), "reason": n.get("reason"),
                             "summary": n.get("summary"),
                             "revisited_by": [self.g.nodes[e["dst"]]["number"] for e in self.g.out(i, "REVISITED_BY")]}
                            for _, i, n in ideas[:6]],
        }
