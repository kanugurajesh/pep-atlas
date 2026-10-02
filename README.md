# PEP Atlas: a precedent engine for Python typing proposals

**Domain A (Language Evolution), focused on the typing PEPs.**

> **Try it in 60 seconds** (Python 3.10+, offline, no API keys)
> ```bash
> pip install -r requirements.txt
> python -m pepatlas assess "Allow T? as a shorthand for Optional[T] in annotations"   # verdict: previously rejected, with PEP 645's reason
> python -m pepatlas explain "Why are there both TypeGuard and TypeIs?"                  # lineage of a concept, with the alternatives turned down
> ```
> Then open [`knowledge/graph.html`](knowledge/graph.html) in a browser and click any node to see its edges and the sentence each one came from.
>
> **Measured, not just demoed:** on a time-based hold-out, concept anchoring improves the rank of the first right PEP over plain text search (MRR 0.70 → 0.81). Verdicts are scored on 40 hand-labelled proposals: a dev set of 26 that exposed failure patterns, and a hold-out set of 14 frozen before any rule was changed. The expected PEP is among the first three cited in 28 of 30 cases. The single-label verdict is the weak step (8/14 on the hold-out), and [approach.md §5–6](approach.md#5-evaluation) explains why, including one fix kept and one tried and not applied. 41 tests, deterministic build.

You describe a typing feature you're thinking of proposing, in plain English. PEP Atlas reasons over a knowledge graph built from 55 typing PEPs and tells you:

- **whether it has been tried**: verdicts are *already exists*, *in progress*, *previously rejected*, *rejected as an alternative inside another PEP*, *builds on an existing area* and *outside known territory*
- **what happened**: the decision and its recorded rationale, quoted from the source
- **which objections to prepare for**: concern types that reviewers raised against similar ideas, each with a quote and its PEP section
- **what to read first**: prior PEPs ordered as a curriculum, from foundations to the closest work
- **who to talk to and where**: the authors, sponsors and delegates active in that area, plus the venue
- **warnings** when the idea runs into a *stated non-goal*, e.g. "no desire to ever make type hints mandatory" from PEP 484

Every claim in the output traces back to a graph edge, and every edge records the PEP section and evidence sentence it came from. There is no LLM and no NLP library anywhere: the entity schema, lexicon and mapping rules are all hand-written (see [approach.md](approach.md)).

```
$ python -m pepatlas assess "Allow T? as a shorthand for Optional[T] in annotations"

## Verdict: Previously rejected  (confidence: high)
PEP 645 (Allow writing optional types as x?) proposed this and was withdrawn. ...
- decision: "The notation T|None introduced by 604 to write Optional[T] is a fine
  alternative to T? and does not require new syntax. Using T? to mean T|None is also
  inconsistent with TypeScript where it roughly means NotRequired[T]. ..."
```

## Quick start

Requires Python 3.10+ (tested on 3.13). No API keys, no network access needed after cloning.

```bash
pip install -r requirements.txt          # only `rich` (pretty terminal output) and `pytest`
python -m pepatlas assess "Add a shorthand syntax for callable types like (int, str) -> bool"
```

The knowledge state (`knowledge/`) is committed, so `assess` and `explain` work immediately.

## Commands

| Command | What it does |
|---|---|
| `python -m pepatlas assess "<proposal>"` | Assess a new proposal. Also accepts `--file proposal.txt` or stdin. `--json` gives machine-readable output; `--plain` gives raw Markdown. |
| `python -m pepatlas explain "<question>"` | "Why does X work this way?" Shows the concept's lineage through PEPs and the alternatives turned down along the way. |
| `python -m pepatlas inspect pep 604` | Shows a node and all its edges with provenance. Kinds: `pep`, `concept`, `person`, `idea`, `concern`, `id`. |
| `python -m pepatlas build` | Rebuilds the whole knowledge state from `data/raw/` (about 10 s, deterministic). |
| `python -m pepatlas eval` | Temporal hold-out retrieval evaluation plus the verdict benchmark (dev set `eval/verdict_cases.json`, hold-out `eval/verdict_cases_holdout.json`), writes `eval/results.md`. |
| `python -m pepatlas fetch` | Re-downloads the PEP sources at the pinned commit (needs git and network access; only needed to refresh `data/raw/`). |
| `python -m pytest` | 41 tests: parser, lexicon rules, extraction checked against known typing history, reasoning golden cases, output precision and grounding, benchmark case validity, build determinism (also across hash seeds). |

Try the inputs in [`examples/`](examples/). Each `NN_*.txt` has its generated `.out.md` and `.out.json` next to it.

```bash
python -m pepatlas assess --file examples/04_runtime_enforcement.txt
python -m pepatlas explain "Why are there both TypeGuard and TypeIs?"
```

## The knowledge state (inspectable without running code)

| File | What it is |
|---|---|
| [`knowledge/graph.json`](knowledge/graph.json) | **The** knowledge base: the schema, 494 nodes and 1,847 typed edges. Each edge has `source`, `section`, `evidence` and `confidence`. The reasoner reads only this file. |
| [`knowledge/summary.md`](knowledge/summary.md) | A readable tour: concept lineages (who introduced, extended or proposed each concept), every PEP's focus and foundations, rejected ideas that were later revisited, and objection statistics. |
| [`knowledge/graph.html`](knowledge/graph.html) | An interactive viewer. Open it in a browser, click any node, and see its attributes and every edge with its evidence quote. (vis-network loads from a CDN.) |
| [`knowledge/schema.json`](knowledge/schema.json) | Node and edge types, with the rule that produces each edge type. |

To regenerate everything: `python -m pepatlas build`. The output is byte-for-byte deterministic, and a test enforces this.

## Project structure

```
pepatlas/
  config.py      paths, pinned source commit, corpus definition
  fetch.py       clone python/peps at the pinned commit, vendor the typing subset
  parse.py       purpose-built RST reader: headers, section tree, prose extraction
  lexicon.py     hand-curated concepts (64), concern taxonomy (10), section semantics, intent rules
  extract.py     mapping rules -> typed nodes/edges with provenance (6 passes)
  graph.py       graph container, schema, deterministic JSON (de)serialization
  textindex.py   small pure-Python TF-IDF (secondary signal only)
  reasoner.py    profile -> anchor -> expand -> decide; `assess` and `explain`
  report.py      Markdown rendering
  export.py      graph.json, schema.json, summary.md;  viewer.py: graph.html
  evaluate.py    temporal hold-out evaluation with ablations
  cli.py         command-line interface
data/raw/        the 55 vendored PEP sources + SOURCE.md (repo, commit, license) + all PEP titles
knowledge/       the generated knowledge state (committed)
examples/        sample inputs and generated outputs
eval/results.md  evaluation results
tests/           pytest suite
```

## Configuration

There are no environment variables and no secrets. The tunables are named constants with comments at the top of `pepatlas/reasoner.py` (scoring weights and verdict thresholds) and `pepatlas/extract.py` (focus rules). The corpus definition (`Topic: Typing` header plus 6 named extra PEPs) and the pinned commit are in `pepatlas/config.py`.

## Data

The data is [python/peps](https://github.com/python/peps) at commit `f92659f`: all 49 PEPs tagged `Topic: Typing`, plus 6 untagged PEPs that belong to the typing story (3107, 557, 637, 645, 661, 712). PEPs are public domain / CC0. See [`data/raw/SOURCE.md`](data/raw/SOURCE.md).
