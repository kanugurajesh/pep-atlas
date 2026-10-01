"""Command-line interface.

  python -m pepatlas build                 rebuild knowledge/ from data/raw
  python -m pepatlas assess "<proposal>"   assess a new proposal (or --file, or stdin)
  python -m pepatlas explain "<question>"  lineage of a behaviour / concept
  python -m pepatlas inspect pep 604       look at what the graph knows about a node
  python -m pepatlas eval                  temporal hold-out evaluation
  python -m pepatlas fetch                 re-vendor the raw PEPs at the pinned commit
"""
from __future__ import annotations

import argparse
import json
import sys

from .config import GRAPH_PATH


def _console_print(md: str, plain: bool):
    if plain:
        print(md)
        return
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        Console().print(Markdown(md))
    except ImportError:
        print(md)


def _read_input(args) -> str:
    if args.file:
        return open(args.file, encoding="utf-8").read()
    if args.text:
        return " ".join(args.text)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    sys.exit("Provide the input as an argument, with --file, or on stdin.")


def _engine():
    from .graph import KnowledgeGraph
    from .reasoner import Engine
    if not GRAPH_PATH.exists():
        sys.exit(f"{GRAPH_PATH} not found. Run `python -m pepatlas build` first.")
    return Engine(KnowledgeGraph.load(GRAPH_PATH))


def cmd_build(args):
    from .export import write_all
    from .extract import build_graph
    g = build_graph()
    write_all(g)
    stats = g.to_json()["stats"]
    print(f"Wrote {GRAPH_PATH}: {sum(stats['nodes'].values())} nodes, {sum(stats['edges'].values())} edges")


def cmd_assess(args):
    from .report import assessment_md
    result = _engine().assess(_read_input(args))
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _console_print(assessment_md(result), args.plain)


def cmd_explain(args):
    from .report import explanation_md
    result = _engine().explain(_read_input(args))
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _console_print(explanation_md(result), args.plain)


def cmd_inspect(args):
    from .graph import KnowledgeGraph
    g = KnowledgeGraph.load(GRAPH_PATH)
    prefix = {"pep": "pep:", "concept": "concept:", "person": "person:", "idea": "idea:", "concern": "concern:"}
    node_id = prefix.get(args.kind, "") + args.key if args.kind != "id" else args.key
    if node_id not in g.nodes:
        matches = [n for n in g.nodes if n.startswith(node_id)]
        if len(matches) != 1:
            sys.exit(f"No unique node for {node_id!r}. Candidates: {matches[:15]}")
        node_id = matches[0]
    node = dict(g.nodes[node_id])
    for k in ("text",):
        node.pop(k, None)
    print(json.dumps(node, indent=2, ensure_ascii=False))
    print("\nOutgoing:")
    for e in sorted(g.out(node_id), key=lambda e: (e["type"], e["dst"])):
        print(f"  -{e['type']}-> {g.label(e['dst'])}   [{e.get('section', '')}]")
    print("Incoming:")
    for e in sorted(g.into(node_id), key=lambda e: (e["type"], e["src"])):
        print(f"  <-{e['type']}- {g.label(e['src'])}")


def cmd_eval(args):
    from .evaluate import run
    print(run())


def cmd_fetch(args):
    from .fetch import run
    run()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pepatlas", description="Precedent engine for Python typing proposals")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build", help="rebuild the knowledge state from data/raw").set_defaults(fn=cmd_build)
    sub.add_parser("fetch", help="re-vendor PEP sources at the pinned commit").set_defaults(fn=cmd_fetch)
    sub.add_parser("eval", help="temporal hold-out evaluation -> eval/results.md").set_defaults(fn=cmd_eval)
    for name, fn, helptext in (("assess", cmd_assess, "assess a new typing proposal"),
                               ("explain", cmd_explain, "explain how a typing behaviour came to be")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("text", nargs="*")
        p.add_argument("--file", "-f")
        p.add_argument("--json", action="store_true", help="machine-readable output")
        p.add_argument("--plain", action="store_true", help="raw markdown, no terminal formatting")
        p.set_defaults(fn=fn)
    p = sub.add_parser("inspect", help="show a node and its edges")
    p.add_argument("kind", choices=["pep", "concept", "person", "idea", "concern", "id"])
    p.add_argument("key")
    p.set_defaults(fn=cmd_inspect)
    args = ap.parse_args(argv)
    args.fn(args)
