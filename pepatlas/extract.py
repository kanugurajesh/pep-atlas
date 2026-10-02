"""Mapping rules: parsed PEP documents -> typed nodes and edges with provenance.

Every rule here is hand-written and documented in approach.md section 2. The
build runs in passes because some relations only make sense once the whole
corpus is known (e.g. "introduces" means *first* accepted PEP focused on a
concept, and "later adopted by" needs every PEP's focus and date).
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from . import lexicon as lx
from .config import PEPS_COMMIT, RAW_DIR
from .graph import KnowledgeGraph
from .parse import PepDocument, first_sentences, load, paragraphs, plain
from .textindex import TfidfIndex

ACCEPTED = {"Final", "Accepted", "Active", "Superseded"}   # Superseded = was accepted, later replaced
FAILED = {"Rejected", "Withdrawn"}
OPEN = {"Draft", "Deferred", "Provisional"}

# Weight of a concept mention by where it occurs. Title and abstract say what a
# PEP is *about*; rejected-ideas text says what it is *not*.
LOCATION_WEIGHT = {"title": 6.0, "abstract": 3.0, "heading": 8.0, "motivation": 1.0, "specification": 1.0,
                   "body": 0.8, "compat": 0.5, "rejected": 0.3, "decision": 0.5, "meta": 0.0}
FOCUS_SHARE = 0.35          # share of the PEP's top concept score needed to count as a focus
MAX_FOCUS = 4
UMBRELLA_HEADINGS = 12      # a PEP with dedicated sections for this many concepts is an umbrella spec

PEP_ROLE_RE = re.compile(r":pep:`(?:[^`<]*<)?(\d+)[^`]*`")
PEP_TEXT_RE = re.compile(r"\bPEP[\s-]*0*(\d{1,4})\b")


def outcome_class(status: str) -> str:
    if status in ACCEPTED:
        return "accepted"
    if status in FAILED:
        return "failed"
    return "open"


def slug(text: str, n: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n]


def pid(number: int) -> str:
    return f"pep:{number}"


def parse_date(s: str) -> str | None:
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def split_people(value: str) -> list[tuple[str, str | None]]:
    people = []
    for part in re.split(r",\s*(?![^<]*>)", value):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.*?)\s*<([^>]+)>\s*$", part)
        name, email = (m.group(1), m.group(2)) if m else (part, None)
        name = re.sub(r"\s+", " ", name).strip().strip('"')
        if name:
            people.append((name, email))
    return people


def venue_of(value: str) -> tuple[str, str] | None:
    v = value.lower()
    if "discuss.python.org" in v:
        return "venue:discourse", "discuss.python.org (Discourse)"
    if "typing-sig" in v:
        return "venue:typing-sig", "typing-sig mailing list"
    if "python-dev" in v:
        return "venue:python-dev", "python-dev mailing list"
    if "python-ideas" in v:
        return "venue:python-ideas", "python-ideas mailing list"
    return None


def load_titles() -> dict[int, str]:
    path = RAW_DIR.parent / "pep_titles.tsv"
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            n, _, t = line.partition("\t")
            out[int(n)] = t
    return out


_GENERIC_WORDS = {"rejected", "alternative", "alternatives", "idea", "ideas", "proposal", "proposals", "considered",
                  "other", "and", "or", "deferred", "postponed", "discarded", "approaches", "options", "non-goals"}


def is_generic_heading(title: str) -> bool:
    """'Rejected Ideas', 'Rejected/Postponed Proposals', ... say nothing about the idea itself."""
    return all(w in _GENERIC_WORDS for w in re.split(r"[\s/]+", title.lower().strip()) if w)


def clean_title(t: str) -> str:
    return plain(t).replace("\\*", "*").strip()


# =================================================================== builder


class Builder:
    def __init__(self, docs: list[PepDocument]):
        self.docs = sorted(docs, key=lambda d: d.number)
        self.by_num = {d.number: d for d in self.docs}
        self.g = KnowledgeGraph()
        self.titles = load_titles()
        self.concept_scores: dict[int, dict[str, float]] = {}
        self.concept_counts: dict[int, Counter] = {}
        self.focus: dict[int, list[str]] = {}
        self.headed: dict[int, set[str]] = {}

    # ------------------------------------------------------------ pass 1
    def add_peps(self):
        for d in self.docs:
            h = d.headers
            status = h.get("Status", "?")
            created = parse_date(h.get("Created", ""))
            abstract = d.top_level("Abstract")
            self.g.add_node(
                pid(d.number), "PEP", number=d.number, title=clean_title(h.get("Title", "")),
                status=status, outcome=outcome_class(status), pep_type=h.get("Type"),
                created=created, year=int(created[:4]) if created else None,
                python_version=h.get("Python-Version"), in_corpus=True,
                abstract=first_sentences(abstract.own_text, 500) if abstract else "",
                outline=[clean_title(s.title) for s in d.sections() if s.level <= 2
                         and lx.section_kind(s.path) not in ("meta", "decision")],
                url=f"https://peps.python.org/pep-{d.number:04d}/",
                source_file=f"data/raw/peps/pep-{d.number:04d}.rst",
            )
        for cid, (label, _) in lx.CONCERNS.items():
            self.g.add_node(f"concern:{cid}", "Concern", label=label)
        for c in lx.CONCEPTS:
            self.g.add_node(f"concept:{c.id}", "Concept", label=c.label, category=c.category,
                            description=c.description, lexicon_idents=list(c.idents),
                            lexicon_phrases=list(c.phrases))

    def stub_pep(self, number: int) -> str:
        node = pid(number)
        if node not in self.g.nodes:
            self.g.add_node(node, "PEP", number=number, title=clean_title(self.titles.get(number, "?")),
                            in_corpus=False, url=f"https://peps.python.org/pep-{number:04d}/")
        return node

    # ------------------------------------------------------------ pass 2: header relations
    def add_header_relations(self):
        for d in self.docs:
            h, src = d.headers, pid(d.number)
            for role, edge in (("Author", "AUTHORED_BY"), ("Sponsor", "SPONSORED_BY")):
                for i, (name, email) in enumerate(split_people(h.get(role, ""))):
                    person = self.person(name, email)
                    self.g.add_edge(src, person, edge, confidence=1.0, source=src, section=f"header:{role}",
                                    order=i)
            for rel, edge in (("Requires", "REQUIRES"), ("Replaces", "REPLACES"), ("Superseded-By", "SUPERSEDED_BY")):
                for n in re.findall(r"\d+", h.get(rel, "")):
                    self.g.add_edge(src, self.stub_pep(int(n)), edge, confidence=1.0, source=src,
                                    section=f"header:{rel}")
            for v in re.split(r",\s*", h.get("Python-Version", "")):
                if v.strip():
                    ver = self.g.add_node(f"python:{v.strip()}", "PythonVersion", label=f"Python {v.strip()}")
                    self.g.add_edge(src, ver, "TARGETS", confidence=1.0, source=src, section="header:Python-Version")
            venue = venue_of(h.get("Discussions-To", ""))
            if venue:
                self.g.add_node(venue[0], "Venue", label=venue[1])
                self.g.add_edge(src, venue[0], "DISCUSSED_AT", confidence=1.0, source=src,
                                section="header:Discussions-To", url=h.get("Discussions-To"))
            self.add_decision(d)

    def person(self, name: str, email: str | None) -> str:
        node = f"person:{slug(name)}"
        existing = self.g.get(node)
        emails = set(existing.get("emails", [])) if existing else set()
        if email:
            emails.add(email.lower())
        return self.g.add_node(node, "Person", name=name, emails=sorted(emails))

    def add_decision(self, d: PepDocument):
        h, status = d.headers, d.headers.get("Status", "?")
        if status in OPEN:
            return
        src = pid(d.number)
        node = f"decision:{d.number}"
        texts, sections = [], []
        # Some decisions live in an admonition before the first heading.
        preamble = "\n".join(l.strip() for l in d.root.own_text.splitlines() if not l.lstrip().startswith(".. "))
        if re.search(r"\b(?:rejected|withdrawn)\b", preamble, re.IGNORECASE):
            texts += paragraphs(preamble)
            sections.append("(preamble note)")
        for s in d.sections():
            if lx.section_kind([s.title]) == "decision" and s.level <= 2:
                texts += paragraphs(s.own_text)
                sections.append(s.title)
        rationale = " ".join(texts)[:900]
        self.g.add_node(node, "Decision", label=f"PEP {d.number} {status.lower()}", outcome=status,
                        outcome_class=outcome_class(status), resolution_url=h.get("Resolution"),
                        rationale=rationale or None, rationale_sections=sections)
        self.g.add_edge(src, node, "HAS_DECISION", confidence=1.0, source=src, section="header:Status")
        for role in ("BDFL-Delegate", "PEP-Delegate"):
            for name, email in split_people(h.get(role, "")):
                self.g.add_edge(node, self.person(name, email), "DECIDED_BY", confidence=1.0, source=src,
                                section=f"header:{role}")
        if rationale and outcome_class(status) == "failed":
            for cid, sent in lx.classify_concerns(texts).items():
                self.g.add_edge(src, f"concern:{cid}", "RAISES", confidence=0.7, source=src,
                                section=" / ".join(sections), evidence=sent, context="decision")

    # ------------------------------------------------------------ pass 3: concepts
    def score_concepts(self):
        for d in self.docs:
            title = d.headers.get("Title", "")
            weighted: dict[str, float] = defaultdict(float)
            counts: Counter = Counter()
            headed: set[str] = set()
            for cid, n in lx.count_concepts(title).items():
                weighted[cid] += LOCATION_WEIGHT["title"] * n
                counts[cid] += n
            for s in d.sections():
                kind = lx.section_kind(s.path)
                loc = kind if kind in LOCATION_WEIGHT else "body"
                if kind == "abstract":
                    loc = "abstract"
                hits = lx.count_concepts(s.own_text)
                for cid, n in hits.items():
                    weighted[cid] += LOCATION_WEIGHT[loc] * min(n, 8)   # cap: one code-heavy section can't dominate
                    counts[cid] += n
                # A dedicated (non-rejected) section heading is strong evidence of focus.
                if kind not in ("rejected", "meta", "decision"):
                    for cid in lx.concepts_in_heading(s.title):
                        weighted[cid] += LOCATION_WEIGHT["heading"]
                        headed.add(cid)
            self.concept_scores[d.number] = dict(weighted)
            self.headed[d.number] = headed
            self.concept_counts[d.number] = counts

    def add_concept_relations(self):
        order = sorted(self.docs, key=lambda d: (self.g.nodes[pid(d.number)]["created"] or "", d.number))
        introduced: dict[str, int] = {}
        for d in order:
            node = self.g.nodes[pid(d.number)]
            scores = self.concept_scores[d.number]
            if not scores:
                self.focus[d.number] = []
                continue
            top = max(scores.values())
            in_title = set(lx.count_concepts(d.headers.get("Title", "")))
            focus = sorted((c for c, w in scores.items() if w >= FOCUS_SHARE * top and w >= 6),
                           key=lambda c: (-scores[c], c))[:MAX_FOCUS]
            # Whatever the title names is always a focus, whatever the counts say.
            focus += sorted(in_title - set(focus))
            if len(self.headed[d.number]) >= UMBRELLA_HEADINGS:
                # Umbrella PEP (in practice: 484). It defines a whole vocabulary
                # with one section per construct, so every concept that has its
                # own heading is a focus, not just the top few by count.
                focus = sorted(set(focus) | self.headed[d.number], key=lambda c: (-scores[c], c))
            self.focus[d.number] = focus
            node["focus_concepts"] = focus
            for cid, w in sorted(scores.items()):
                cnt = self.concept_counts[d.number][cid]
                target = f"concept:{cid}"
                share = round(w / top, 3)
                if cid in focus and node["pep_type"] == "Standards Track":
                    if node["outcome"] == "accepted":
                        etype = "EXTENDS" if cid in introduced else "INTRODUCES"
                        introduced.setdefault(cid, d.number)
                    else:
                        etype = "PROPOSES"
                    conf = 0.85
                elif cnt >= 2 or w >= 3:
                    etype, conf = "MENTIONS", 0.6
                else:
                    continue
                self.g.add_edge(pid(d.number), target, etype, confidence=conf, source=pid(d.number),
                                weight=share, mentions=cnt,
                                rule="focus: title/abstract/heading-weighted share >= %.2f" % FOCUS_SHARE
                                if etype != "MENTIONS" else "lexicon mentions")

    # ------------------------------------------------------------ pass 4: PEP-PEP references
    def add_references(self):
        for d in self.docs:
            src = pid(d.number)
            src_created = self.g.nodes[src]["created"] or ""
            per_target: dict[int, Counter] = defaultdict(Counter)
            evidence: dict[int, tuple[str, str]] = {}
            for s in d.sections():
                kind = lx.section_kind(s.path)
                raw = s.own_text
                nums = [int(n) for n in PEP_ROLE_RE.findall(raw)]
                nums += [int(n) for n in PEP_TEXT_RE.findall(PEP_ROLE_RE.sub(" ", raw))]
                for n in nums:
                    if n == d.number or n == 0:
                        continue
                    per_target[n][kind] += 1
                    if n not in evidence or (kind != "meta" and evidence[n][0] == "meta"):
                        sent = next((x for p in paragraphs(raw) for x in lx.split_sentences(p)
                                     if re.search(rf"\b0*{n}\b", x)), "")
                        evidence[n] = (kind, " / ".join(s.path), sent)
            for n, kinds in sorted(per_target.items()):
                dst = self.stub_pep(n)
                dnode = self.g.nodes[dst]
                total = sum(kinds.values())
                rejected = kinds.get("rejected", 0)
                foundational = sum(kinds[k] for k in ("abstract", "motivation", "specification", "body", "compat"))
                if rejected and rejected >= foundational:
                    etype = "CONTRASTS_WITH"
                elif (dnode.get("in_corpus") and dnode.get("outcome") == "accepted"
                      and (dnode.get("created") or "") < src_created and foundational):
                    etype = "BUILDS_ON"
                else:
                    etype = "REFERENCES"
                _, section, sent = evidence.get(n, ("", "", ""))
                self.g.add_edge(src, dst, etype, confidence=0.9 if etype != "REFERENCES" else 0.8, source=src,
                                section=section, evidence=sent, count=total, by_section=dict(sorted(kinds.items())))

    # ------------------------------------------------------------ pass 5: rejected ideas, concerns, tools
    def add_rejected_ideas(self):
        for d in self.docs:
            src = pid(d.number)
            seen_containers = set()
            for s in d.sections():
                if not lx.REJECTED_HEADING_RE.search(s.title) or lx.section_kind([s.title]) == "decision":
                    continue
                if any(id(a) in seen_containers for a in self._ancestors(s)):
                    continue
                seen_containers.add(id(s))
                leaves = [x for x in s.walk() if not x.children and x is not s] or [s]
                for leaf in leaves:
                    self.add_idea(d, src, leaf, container=s)
            # Concerns raised in a PEP's own compat / open-issues sections.
            for s in d.sections():
                kind = lx.section_kind(s.path)
                if kind in ("compat", "open_issues"):
                    for cid, sent in lx.classify_concerns(paragraphs(s.own_text)).items():
                        self.g.add_edge(src, f"concern:{cid}", "RAISES", confidence=0.5, source=src,
                                        section=" / ".join(s.path), evidence=sent, context=kind)
            # Tools
            tool_hits: dict[str, tuple[str, int, str]] = {}
            for s in d.sections():
                kind = lx.section_kind(s.path)
                for tool, n in lx.find_tools(plain(s.own_text)).items():
                    etype = "IMPLEMENTED_IN" if kind == "reference_impl" else "MENTIONS_TOOL"
                    prev = tool_hits.get(tool)
                    if prev is None or (etype == "IMPLEMENTED_IN" and prev[0] != etype):
                        tool_hits[tool] = (etype, n + (prev[1] if prev else 0), " / ".join(s.path))
                    else:
                        tool_hits[tool] = (prev[0], prev[1] + n, prev[2])
            for tool, (etype, n, section) in sorted(tool_hits.items()):
                node = self.g.add_node(f"tool:{tool}", "Tool", label=tool)
                self.g.add_edge(src, node, etype, confidence=0.8, source=src, section=section, mentions=n)

    @staticmethod
    def _ancestors(s):
        p = s.parent
        while p is not None:
            yield p
            p = p.parent

    def add_idea(self, d: PepDocument, src: str, s, container):
        title = clean_title(s.title)
        if is_generic_heading(title):
            # A generic "Rejected alternatives" heading: name it after what it is an alternative *to*.
            if s.parent is not None and s.parent.level > 0:
                title = f"{clean_title(s.parent.title)}: {title.lower()}"
            else:
                title = f"{title} (PEP {d.number})"
        text = s.full_text()
        paras = paragraphs(text)
        if not paras:
            return
        node = base = f"idea:{d.number}:{slug(s.title)}"
        k = 2
        while node in self.g.nodes:          # two sub-sections may share a heading
            node, k = f"{base}-{k}", k + 1
        sentences = [x for p in paras for x in lx.split_sentences(p)]
        reasons, used = [], set()
        for i, x in enumerate(sentences):
            if len(reasons) == 2:
                break
            if i not in used and lx.REASON_CUES.search(x):
                # "We rejected this because:" is followed by the actual list.
                if x.endswith(":") and i + 1 < len(sentences):
                    x += " " + sentences[i + 1]
                    used.add(i + 1)
                reasons.append(x)
        kind = "non_goal" if re.search(r"non-?goal|out of scope", " ".join(s.path), re.IGNORECASE) else "alternative"
        if kind == "non_goal" and s is container:
            title = f"Stated non-goals of PEP {d.number}"
        self.g.add_node(node, "RejectedIdea", title=title, pep=d.number, section=" / ".join(s.path), kind=kind,
                        summary=first_sentences(text, 360), reason=" ".join(reasons)[:600] or None,
                        text=" ".join(paras)[:2500], year=self.g.nodes[src]["year"])
        self.g.add_edge(src, node, "CONSIDERED", confidence=1.0, source=src, section=" / ".join(s.path))
        # ABOUT: what the idea is about. The heading counts most.
        scores: Counter = Counter()
        for cid, n in lx.count_concepts(s.title).items():
            scores[cid] += 4 * n
        for cid, n in lx.count_concepts(text).items():
            scores[cid] += min(n, 5)
        for cid, w in scores.most_common(3):
            if w >= 2:
                self.g.add_edge(node, f"concept:{cid}", "ABOUT", confidence=0.8 if w >= 4 else 0.6, source=src,
                                section=" / ".join(s.path), weight=w)
        for cid, sent in lx.classify_concerns(paras).items():
            self.g.add_edge(node, f"concern:{cid}", "RAISES", confidence=0.6, source=src,
                            section=" / ".join(s.path), evidence=sent, context="rejected_idea")

    # ------------------------------------------------------------ pass 6: derived
    def add_revisits(self):
        """A rejected idea is 'later adopted' when a PEP that was created after
        the rejecting PEP and accepted (1) is focused on a concept the idea is
        strongly about, (2) cites the rejecting PEP, and (3) has a title and
        abstract lexically close to the idea. (2) can be waived only for a very
        close wording match. Each condition alone is too loose: TypeVar is
        everywhere, and wording overlap alone is noisy."""
        peps = {n["id"]: n for n in self.g.of_type("PEP") if n.get("in_corpus")}
        index = TfidfIndex({p: f"{n['title']} {n['title']} {n.get('abstract', '')}" for p, n in peps.items()})
        pep_links = {(e["src"], e["dst"]) for e in self.g.edges
                     if e["type"] in ("BUILDS_ON", "CONTRASTS_WITH", "REFERENCES", "REPLACES", "REQUIRES")}
        for idea in self.g.of_type("RejectedIdea"):
            about = {e["dst"][8:] for e in self.g.out(idea["id"], "ABOUT") if e["weight"] >= 3}
            if not about:
                continue
            origin = peps[pid(idea["pep"])]
            q = index.query_vec(f"{idea['title']} {idea['title']} {idea['summary']}")
            best = None
            for p, n in peps.items():
                if n["outcome"] != "accepted" or (n["created"] or "") <= (origin["created"] or "") or p == origin["id"]:
                    continue
                shared = about & set(self.focus.get(n["number"], []))
                if not shared:
                    continue
                # The later PEP must know the history (cite the rejecting PEP),
                # unless the wording overlap alone is very strong.
                aware = (p, origin["id"]) in pep_links
                sim = index.similarity(q, p)
                if (sim >= 0.30 or (aware and sim >= 0.15)) and (best is None or sim > best[1]):
                    best = (p, sim, shared)
            if best:
                p, sim, shared = best
                self.g.add_edge(idea["id"], p, "REVISITED_BY", confidence=round(min(0.9, 0.4 + sim), 3),
                                source="derived", similarity=round(sim, 3), shared_concepts=sorted(shared),
                                evidence=f"Rejected in PEP {idea['pep']} ({origin['year']}); PEP {peps[p]['number']} "
                                         f"({peps[p]['year']}, {peps[p]['status']}) is focused on "
                                         f"{', '.join(sorted(shared))}")

    def build(self) -> KnowledgeGraph:
        self.add_peps()
        self.add_header_relations()
        self.score_concepts()
        self.add_concept_relations()
        self.add_references()
        self.add_rejected_ideas()
        self.add_revisits()
        self.g.meta = {
            "name": "PEP Atlas: Python typing knowledge graph",
            "source": f"python/peps @ {PEPS_COMMIT}",
            "corpus_peps": sorted(d.number for d in self.docs),
            "builder": "pepatlas.extract (rule-based, no ML/NLP extraction)",
        }
        return self.g


def load_corpus(exclude: set[int] | None = None) -> list[PepDocument]:
    exclude = exclude or set()
    docs = [load(p) for p in sorted(Path(RAW_DIR).glob("pep-*.rst"))]
    return [d for d in docs if d.number not in exclude]


def build_graph(exclude: set[int] | None = None) -> KnowledgeGraph:
    return Builder(load_corpus(exclude)).build()
