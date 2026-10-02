# Approach

## 0. The problem, in one sentence

> *"I want to propose a typing feature. Has it been tried? What happened? What objections will I face? What must I build on, and who should I talk to?"*

Today, answering that means reading dozens of PEPs, each 1,000–3,000 lines, and knowing which "Rejected Ideas" subsection 40 pages deep in which PEP is relevant. PEP Atlas models the typing PEPs as a graph of proposals, concepts, rejected alternatives, objections, decisions and people. When a new proposal comes in, it returns a verdict and a briefing grounded in that graph.

I picked this one problem (the first scenario in the brief) and went deep, rather than covering all three scenarios thinly. The second scenario, *"why does Python behave like this?"*, falls out of the same graph as a small `explain` command. It is a different traversal of the same knowledge, not a separate feature.

## 1. Domain and data subset

**Why Domain A over B and C.**
- **C (Reddit):** API access is now restricted and Pushshift is gone, so sourcing is a risk. The text is also noisy enough that, without NLP tooling (forbidden here), extraction quality would be poor.
- **B (Semantic Scholar):** the API returns citation edges already built, so most of the "relationships" would be someone else's modeling.
- **PEPs are semi-structured:** RFC 822 headers, a section tree with conventional headings ("Rejected Ideas", "Backwards Compatibility", "Non-goals"), and explicit cross-references. That is enough signal for hand-written mapping rules to extract real structure, and the rules themselves become the thing to evaluate.

**Why typing.** It has the richest design history of any PEP area:
- About 50 PEPs over 12 years, all built on each other.
- Real lineages: `Callable` → ParamSpec → the rejected arrow syntax; TypeGuard → withdrawn StrictTypeGuard → TypeIs; stringified annotations → deferred annotations.
- A habit of documenting rejected alternatives in detail. Almost every typing PEP has a "Rejected Ideas" section, and those sections are what make "what objections will I face?" answerable.

**The subset** is 55 PEPs from python/peps, pinned at commit `f92659f`:
- all 49 with the `Topic: Typing` header (an objective, maintainer-assigned selection rule rather than my judgement)
- plus 6 untagged PEPs that belong to the story: 3107 (the annotation syntax typing is built on), 557 (dataclasses, the target of PEP 681), and four failed proposals that predate the Topic header or sit next to it (645, 637, 712, 661).

The 21 PEPs referenced from outside the corpus (e.g. PEP 8, 572) become labelled stub nodes, so no edge dangles. The raw files are vendored in `data/raw/`, so the build is offline and reproducible.

**Not used:** the CPython issue tracker and commit history. Typing *design* reasoning lives in PEPs; implementation commits add volume but very little "why". With limited time, depth on one source beat shallow joins across three (see §7 for when I'd add them).

## 2. The knowledge model

### Entities

| Entity | Count | Where it comes from | Why it is a separate entity |
|---|---|---|---|
| **PEP** | 55 + 21 stubs | headers | The unit of proposal and decision. |
| **Concept** | 64 | hand-curated lexicon (`lexicon.py`) | The shared vocabulary. A new input is mapped onto the same concepts, which is how it "lands" in the graph. Each concept has identifiers (`TypedDict`), prose patterns ("structural subtyping") and a category. |
| **RejectedIdea** | 219 | each leaf sub-section under Rejected Ideas / Alternatives / Why not … / **Non-goals** | **The core of the model.** A PEP's status records only one decision, but its rejected ideas record dozens of smaller ones, each with a reason. That is the most valuable knowledge in the corpus and the hardest to find by hand. |
| **Concern** | 10 | hand-made taxonomy of objection types (backward compat, runtime cost, cost of new syntax, readability, soundness, …) | Turns "these ideas failed" into "this is what reviewers will ask you". Concern nodes let objections be counted and compared across PEPs. |
| **Decision** | 45 | Status + Resolution headers + decision sections (Rejection Notice, PEP Withdrawal, preamble notes) | A decision has its own attributes: outcome, rationale text, decider, resolution link. Folding these into PEP attributes would hide the "why it stopped". |
| **Person** | 55 | Author / Sponsor / Delegate headers, normalized by name and email | Answers "who should I talk to?". |
| **PythonVersion, Venue, Tool** | 13 / 4 / 8 | headers; tool names in Reference Implementation sections | Cheap context with an actionable use: where to discuss, and where reference implementations usually land. |

### Relationships (23 types, all in `knowledge/schema.json` with the rule that produces each)

Key decisions:

1. **PEP→Concept is four relations, not one "about" edge.** `INTRODUCES` (first *accepted* PEP focused on the concept), `EXTENDS` (a later accepted PEP focused on it), `PROPOSES` (a draft, rejected or withdrawn PEP focused on it) and `MENTIONS`. This is what makes lineage questions answerable, e.g. "who introduced TypedDict, who extended it, which TypedDict proposals failed?". It also lets a verdict distinguish "exists" from "was tried". *Focus* is computed from where mentions occur:

   | Where a mention occurs | Weight |
   |---|---|
   | title | 6 |
   | a dedicated section heading | 8 |
   | abstract | 3 |
   | body | 1 |
   | rejected-ideas text | 0.3 |

   A concept is a focus if it reaches 35% of the PEP's top concept score, or if it is named in the title. PEP 484 is detected as an "umbrella" spec (12 or more concepts with their own heading), so each of its sections becomes a focus.

2. **References are typed by the section they appear in.** The `Requires` header occurs exactly once in the corpus, so headers alone give an almost empty graph. Body references are plentiful, but their *meaning* depends on location: a reference from Motivation or Specification to an earlier accepted PEP is `BUILDS_ON`, and a reference from a Rejected Ideas section is `CONTRASTS_WITH`. A test enforces that `BUILDS_ON` always points backwards in time.

3. **Non-goals are rejected ideas of kind `non_goal`.** PEP 484's "no desire to ever make type hints mandatory" is a design *stance*, stronger than a passed-over alternative. The reasoner raises a warning when a proposal runs into one.

4. **`REVISITED_BY` is a derived edge.** It connects a rejected idea to a later accepted PEP that covers the same ground (e.g. PEP 647's rejected "strict narrowing" → PEP 742's `TypeIs`). Three conditions are required:
   - the later PEP focuses on a concept the idea is strongly about
   - it **cites** the rejecting PEP
   - its wording is similar (cosine ≥ 0.15, or ≥ 0.30 without the citation)

   I first called this `LATER_ADOPTED_BY`, then renamed it, because a heuristic can show the ground was revisited but not that the idea was adopted.

5. **Every edge carries provenance:** `source` (PEP), `section` (path in the section tree), `evidence` (the sentence it came from) and `confidence` (by rule type: header 1.0, section-typed reference 0.9, plain reference 0.8, concept focus 0.85, lexicon mention 0.6, derived edges scale with similarity). This is what makes the output auditable, and what lets `graph.html` show the evidence for every edge.

**Deliberately not modeled:**
- **Sentiment or "who argued what" in discussions.** It isn't in the PEP text, and guessing it would be fabrication.
- **A concept hierarchy** (e.g. TypeIs *is-a* narrowing construct). Categories give a coarse grouping; a proper hierarchy is §7 work.
- **Arguments as entities** (claim / counter-claim). PEP prose doesn't mark them reliably enough for rules, and the Concern taxonomy plus the evidence sentence gives 80% of the value.

## 3. How the representation is built, and the tradeoffs

`python -m pepatlas build` runs six passes (`extract.py`). The passes are separate because some relations only make sense once the whole corpus is known: "introduces" means *first*, and "revisited" needs every PEP's focus and date.

1. **PEP nodes:** headers, title, abstract, section outline, Concern and Concept nodes.
2. **Header relations:** people, Requires/Replaces/Superseded-By, Python version, venue, Decision nodes with rationale.
3. **Concept scoring and focus:** `INTRODUCES` / `EXTENDS` / `PROPOSES` / `MENTIONS`, assigned in creation-date order.
4. **PEP→PEP references,** typed by section kind.
5. **Rejected ideas:** `ABOUT` concepts, `RAISES` concerns with evidence sentences, the stated reason, tools.
6. **Derived `REVISITED_BY` edges.**

**Tradeoffs I made on purpose:**
- **I wrote my own RST reader (`parse.py`, about 150 lines) instead of using docutils.** docutils can't resolve the Sphinx-only roles (`:pep:`, `:ref:`) outside the PEP build, and I needed something smaller anyway: headers, a section tree with paths, and prose without code blocks. RST heading levels are assigned by first appearance of each underline style, exactly as in RST.
- **The lexicon is hand-curated: precision over recall.** Identifiers that are also English words (`Final`, `Self`, `Any`, `Literal`, `Protocol`) only count in code context (inline literals, `typing.X`, `X[`, annotation positions). Otherwise "the Final decision" would become an edge. The cost is that unlisted phrasings are missed. This is the system's main recall limit (§6).
- **Typed section semantics are rule-based** (`SECTION_KINDS`). Two bugs taught me to anchor these rules: "Forward references" was being classified as the bibliography section "References", and "Abstract generic types" as the Abstract. Both now have regression tests.
- **TF-IDF is only a secondary signal.** The primary path into the graph is through concepts. Wording similarity covers paraphrase and ideas the lexicon lacks.

**Quality audit (done by hand against known typing history):**
- **`INTRODUCES`:** all 54 checked; 49 correct. Wrong or debatable: 526→runtime annotation access, 563→`TYPE_CHECKING` (really 484), 692→`Unpack` (really 646), 612→`**kwargs` typing, 747→type expressions. The pattern is that a PEP which *formalizes* an existing idea looks like it introduces it.
- **`REVISITED_BY`:** all 18 checked; 11 correct (e.g. 484 "forward declarations" → 649; 612 "list variadics" → 646; 705 "preventing unspecified keys" → 728; 724 "TypeGuard with a second output type" → 742). The 7 wrong ones share a broad concept such as TypedDict without sharing the specific idea. These edges are presented as hints with a confidence value, never as facts. An earlier, looser version produced 34 edges with much lower precision; requiring the later PEP to cite the rejecting one removed most of the noise.
- **Reproducibility:** a test checks that the build is deterministic, and a test checks that every edge has provenance. The determinism test originally rebuilt in the same process, so it could not see an ordering that depends on Python's per-process hash seed. One existed: tied concepts in PEP 484's focus list came out in set order. Sorts now break ties by name, and a second test builds under two hash seeds (0 and 3) that are known to disagree without the fix.
- **A lexicon false positive found through the output:** the bare `T?` pattern matched the English question "Why not use **tool X?**" in PEP 675, so a SQL-tooling idea was linked to the `X?` concept and appeared in the `T?` assessment. A bare `T?` now has to be followed by more code or words. That removed one `ABOUT` edge (1,848 → 1,847).

## 4. What happens when a new input arrives

The reasoner (`reasoner.py`) reads only `knowledge/graph.json`, never the raw files. So everything it says is backed by a node or edge.

1. **Profile.** The same lexicon maps the free text onto Concept nodes, recording the surface form that matched. Rule-based intent detection classifies the kind of change: new syntax, new special form, runtime change, checker semantics, stdlib change. Explicit "PEP NNN" mentions are recorded.
   - Concepts are weighted by **specificity** = 1 / (1 + ln(1 + #PEPs focused on it + ¼ #mentioning)). TypeVar says little about which prior work is relevant; TypeIs says a lot.
   - Concepts with no PEPs yet get no weight, because they say nothing about *which* prior work matters.
2. **Anchor.** Each PEP is scored as
   `0.55 × concept_score + 0.45 × min(1, cosine / 0.4)`.
   - `concept_score` sums, over the input's concepts, specificity × relation strength (introduces/proposes 1.0, extends 0.8, mentions up to 0.3), divided by max(total weight, 0.6).
   - The 0.6 floor stops one broad concept from fully anchoring a match. Without it, every runtime question matched every runtime PEP.
   - Rejected ideas are scored the same way, through `ABOUT` edges weighted by whether the concept is in the idea's own heading.
   - **Rejected ideas must be on topic to be shown.** When the input has concepts, an idea that shares none of them is kept only if its wording overlap is strong (cosine ≥ 0.25) *and* not carried by a single word (no word above 75% of the cosine). Ideas under half the best idea's score are dropped. Without these rules, the word "shorthand" alone (88% of the cosine) pulled PEP 727's slice syntax into the `T?` assessment, and its quotes appeared under "objections".
3. **Expand.** From the anchors the reasoner walks:
   - `SUPERSEDED_BY` / `REPLACES` to find what is in force now
   - `HAS_DECISION` to fetch the recorded rationale
   - `REVISITED_BY` to see whether a rejected idea came back
   - `RAISES` plus the intent priors to produce a ranked objection profile with quotes
   - `BUILDS_ON` / `REQUIRES`, up to two hops, to build a reading list in chronological order. Since `BUILDS_ON` only points backwards in time, sorting by date gives a valid topological order. Each item shows its path, e.g. "foundation of PEP 563 → PEP 604". With unbounded depth the list drifted off-topic (Data Classes as a "foundation" of `X | Y`), so it is capped.
   - `AUTHORED_BY` / `SPONSORED_BY` / `DECIDED_BY`, weighted by relevance and recency, to suggest people
   - `DISCUSSED_AT` of the most recent related PEP, for the venue.
4. **Decide.**
   - **A PEP is a strong match** if its score is ≥ 0.62 and either the wording (cosine ≥ 0.22) or the concepts (≥ 0.8) also match. The verdict then depends on that PEP's outcome: *already exists*, *previously rejected* or *in progress*.
   - **A rejected idea is a strong match** at score ≥ 0.55. The verdict is then *previously rejected as an alternative*, naming the idea and the revisit if there was one.
   - **Otherwise:** *builds on an existing area* if concepts matched, *outside known territory* if not.
   - **Non-goal warnings** are attached whatever the verdict.

**Worked example** (`examples/02_optional_shorthand`). The input "Allow `T?` as a shorthand for `Optional[T]`…" is processed like this:
- **Profile:** the concepts `X?` optional shorthand (specificity 0.55), Union types and `X | Y` syntax; the intent is "new syntax".
- **Anchor:** PEP 645 `PROPOSES` both of the specific concepts, giving score 0.84.
- **Decide:** 645 is Withdrawn, so the verdict is *previously rejected*.
- **Expand:** the Decision node supplies the recorded reason ("`T|None` introduced by 604 is a fine alternative to `T?` and does not require new syntax … inconsistent with TypeScript"). Objections are ranked from the readability, cost-of-new-syntax and ambiguity concerns raised against similar ideas, each quoted with its source. The reading list runs chronologically from 3107 and 484 through 563/585 (what 604 builds on) to 604 and 645.

## 5. Evaluation

**Temporal hold-out** (`python -m pepatlas eval`, full table in `eval/results.md`):
- **Training graph:** the graph is built only from the 36 PEPs created before 2023.
- **Test inputs:** each of the 18 later PEPs that cite earlier work is fed in as a new input. The input is its title and abstract with **every PEP number stripped**, so the answer isn't handed over.
- **Gold set:** the earlier PEPs it actually cites, i.e. the prior work its authors judged relevant.

| Variant | Recall@5 | Recall@10 | MRR |
|---|---|---|---|
| text only (TF-IDF baseline) | 0.53 | 0.64 | 0.70 |
| concepts only (graph) | 0.59 | 0.63 | 0.76 |
| **concepts + text** (closest PEPs, verdict) | 0.54 | 0.65 | **0.81** |
| concepts + text + `BUILDS_ON` propagation | **0.59** | **0.68** | 0.76 |

How to read this: the graph's concept anchoring mainly improves *what comes first* (MRR 0.70 → 0.81). Propagating score along `BUILDS_ON` improves *coverage* (recall@10 0.64 → 0.68): a proposal similar to PEP X is judged against what X built on, even when its wording never mentions it. That trade-off is why the closest-PEP ranking and the verdict use concepts + text, while the reading list adds the `BUILDS_ON` ancestors.

The set is small (18 cases), so differences of a few points are within noise. I tuned only general mechanisms (unknown concepts get no weight, the evidence floor) and not per-case rules.

**Tried and reverted (evidence-driven):**
- **Key-term vocabularies in retrieval.** Adding each PEP's top-150 TF-IDF terms to its retrieval document lowered MRR from 0.81 to 0.76. Reverted.
- **A word-coverage check before "already exists".** I wanted to catch "same area, different mechanism", where the input's distinctive terms are absent from the matched PEP. It flagged generic words ("especially", "without") and missed the real signal ("default", which is common across the corpus). A noisy verdict signal is worse than none, so it is gone. See failure mode 1.
- **A plain cosine floor for off-topic rejected ideas.** It cleaned the six examples, but a test with a shorter `T?` input still let PEP 727's slice idea through: on short inputs, one rare shared word gives a high cosine (0.31). I replaced it with the "strong *and* spread over several words" rule in §4.

**Golden cases** (`tests/test_reasoner.py`): six hand-written proposals with the verdicts a typing practitioner would expect, plus the non-goal warning, grounding checks, and checks that rejected ideas and objection quotes stay on topic. All pass. These cases and the six examples were used while tuning, so they are not evidence of accuracy. That is what the next benchmark is for.

**Verdict benchmark** (`eval/verdict_cases.json`, results in `eval/results.md`):
- **Inputs:** 26 hand-written proposals, about 4 per verdict, paraphrased in plain English with no PEP numbers. Each case states its source of truth (e.g. "PEP 695, Rejected Ideas: Angle Brackets"). One case (a strict TypeGuard) lists a second acceptable verdict, because typing history supports both.
- **Disjoint and frozen:** the cases avoid the golden tests and examples. They were written after the idea-filter thresholds were frozen and before the system was run on them. The numbers below are the **first run**; nothing was tuned against them.

| Metric | Score |
|---|---|
| Verdict exactly right | 14/26 (54%); chance over 6 labels ≈ 17% |
| Right or the listed acceptable alternative | 15/26 (58%) |
| Expected PEP is the first one cited | 14/20 |
| Expected PEP among the first three cited | **18/20** |

How to read this: **retrieval is strong, and the verdict decision is the weak step.** The right PEP is almost always in front of the user, but the single-label decision on top of it is right only about half the time. The failures fall into four patterns, analysed in §6 (items 6–8 and 4). They point at specific rules rather than at the model as a whole, which is what makes them fixable.

## 6. Known limitations (honestly)

1. **Similar is not the same.** "Let TypedDict items declare *default values*" returns *already exists → PEP 655*. PEP 655 covers the vocabulary (NotRequired, missing keys) but not defaults; PEP 589 actually lists default values among things it does not support. The verdict text tells the user to check the specific mechanism, and the output surfaces 589. Telling *mechanism* apart from *area* needs either finer concepts or a semantic model (§7). See `examples/05_typeddict_defaults.out.md`.
2. **Verdicts are only as precise as the best single anchor.** For "infer variance on Protocols" (`examples/06`), the verdict cites PEP 544's rejected idea. The more useful fact, that PEP 695 rejected *explicit* variance because "variance can generally be inferred", is the second hit rather than the headline.
3. **Some decisions happen off-page.** PEP 677's rejection rationale lives in a python-dev post, not in the PEP. The report says so and links the resolution, but cannot summarize it.
4. **Lexicon recall.** Paraphrases the lexicon doesn't list ("TypedDict inline" was missing until a test caught it) fall back to wording similarity. The verdict benchmark measures this: 4 of the 12 misses recognised **no concept at all** in plain-English descriptions of well-known features. Examples are "returns an instance of whatever class it was called on" (Self), "the parameter list of the function it wraps" (ParamSpec) and "explicit type arguments in square brackets" (PEP 718).
5. **The concern classifier is cue-based.** "Readability" is the most frequent concern partly because its cues ("confusing", "learn") are common words. It suits ranking and quoting, not statistics.
6. **Wording alone can claim "already exists".** When no concept is recognised, the verdict rests on TF-IDF alone, and a strong word overlap can cross the threshold. "Speed up dictionary lookups by caching hashes of string keys" was answered *already exists → PEP 589 (TypedDict)*. A rule saying "no concept → never claim an exact precedent" is the obvious fix. I have not applied it, because the benchmark is frozen and it would be tuned on the case it fixes. It goes into the next round with new cases.
7. **An accepted PEP pre-empts its own rejected alternatives.** "Make `isinstance(x, list[int])` check elements" matches PEP 585 strongly, so the verdict says *already exists*, even though the specific mechanism is one of 585's rejected alternatives. The same happens with "make every class a protocol" (PEP 544). The decision rule checks PEP matches before idea matches. It should prefer the idea when the idea is a strong match *and* lives inside the matched PEP.
8. **Correct anchor, cautious verdict.** For TypeIs (PEP 742), explicit variance (PEP 695) and keyword indexing (PEP 637), the right PEP is cited first or second, but the score sits under the strong-match threshold (e.g. 0.57 vs 0.62), so the verdict falls back to *builds on an existing area*. The fallback is safe, since it never claims a false precedent, but it under-claims.

## 7. What I would build next, and why

1. **Ingest the Resolution threads and Discourse discussions** linked from the headers (35 resolution links, 48 discussion links). This closes limitation 3, and it is where *who objected and why* lives: Person -RAISED-> Concern edges with real attribution. It's the highest-value addition.
2. **A concept hierarchy and finer mechanisms** (e.g. TypedDict → {totality, read-only, extra items, defaults}). This attacks limitation 1 directly. Concepts become specific enough that "same area, different mechanism" is visible in the graph rather than guessed from words.
3. **Fix the verdict rule using the benchmark's failure patterns, on a fresh test set.** The first benchmark (§5) shows the decision step, not retrieval, is the weak link, and §6 items 6–8 name the specific rules. I would fix them, then grow the case set with 30–50 proposals sampled from real typing-sig / Discourse "Ideas" threads, labelled with what actually happened. The current 26 cases would then become the dev set. Reporting fixes on the cases that motivated them would overstate the gain.
4. **The CPython `typing` module history** (`Lib/typing.py` commits, typing_extensions releases). Adds an "implemented in version X / runtime behavior changed in Y" layer, useful for the *why does Python behave like this* scenario.
5. **An optional LLM layer on the output side only:** turning the already-grounded JSON briefing into prose, constrained to cite edge evidence. Extraction stays rule-based. The graph remains the source of truth, and the model never decides what is known.
