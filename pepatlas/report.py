"""Render reasoner output as Markdown (for the terminal and for examples/)."""
from __future__ import annotations

VERDICT_TITLES = {
    "already_exists": "Already exists",
    "previously_rejected": "Previously rejected",
    "in_progress": "Already in progress",
    "previously_rejected_alternative": "Previously rejected as an alternative",
    "extends_existing_area": "Builds on an existing area (no direct precedent)",
    "outside_known_territory": "Outside known territory",
}


ROLE_NAMES = {"author": "author of", "sponsor": "sponsor of", "delegate": "decision delegate for"}


def _q(text: str | None, n: int = 320) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def assessment_md(r: dict) -> str:
    v = r["verdict"]
    L = [f"# Proposal assessment", "", f"> {_q(r['input']['text'], 400)}", ""]
    L += [f"## Verdict: {VERDICT_TITLES[v['label']]}  (confidence: {v['confidence']})", "", v["summary"], ""]
    for w in v.get("warnings", []):
        L += [f"> ⚠ {_q(w, 400)}", ""]

    concepts = r["input"]["concepts"]
    L += ["## How the input was read", ""]
    if concepts:
        L += ["| Concept | Matched on | Specificity |", "|---|---|---|"]
        cell = lambda x: x.replace("|", r"\|")
        L += [f"| {cell(c['label'])} | {cell(', '.join(c['matched'][:3]))} | {c['specificity']} |" for c in concepts]
    else:
        L += ["No lexicon concepts recognised; matching relied on wording only."]
    if r["input"]["intents"]:
        L += ["", "Kind of change: " + ", ".join(i.replace("_", " ") for i in r["input"]["intents"])]
    L.append("")

    L += ["## Closest prior PEPs", ""]
    for p in r["closest_peps"]:
        sup = f" → superseded by {', '.join('PEP %d' % s for s in p['superseded_by'])}" if p["superseded_by"] else ""
        L.append(f"- **PEP {p['pep']}: {p['title']}** ({p['status']}, {p['year']}){sup}, score {p['score']}")
        L.append(f"  - why: {'; '.join(p['why'])}")
        if p.get("decision") and p["status"] in ("Rejected", "Withdrawn"):
            d = p["decision"]
            if d.get("rationale"):
                L.append(f"  - decision: \"{_q(d['rationale'], 300)}\"")
            elif d.get("resolution"):
                L.append(f"  - decision rationale is not in the PEP text; see the resolution: {d['resolution']}")
    L.append("")

    if r["rejected_ideas"]:
        L += ["## Similar ideas that were turned down", ""]
        for i in r["rejected_ideas"]:
            L.append(f"- **{i['idea']}** (PEP {i['pep']} § {i['section']}, {i['year']}), score {i['score']}")
            if i.get("reason"):
                L.append(f"  - stated reason: \"{_q(i['reason'])}\"")
            elif i.get("summary"):
                L.append(f"  - context: \"{_q(i['summary'])}\"")
            if i["concerns"]:
                L.append(f"  - concern types: {', '.join(i['concerns'])}")
            for rv in i["revisited_by"]:
                L.append(f"  - ↻ later revisited by **PEP {rv['pep']}** ({rv['title']}, {rv['status']})")
        L.append("")

    if r["objections_to_prepare_for"]:
        L += ["## Objections to prepare for", ""]
        for c in r["objections_to_prepare_for"]:
            tag = f" (typical for: {', '.join(x.replace('_', ' ') for x in c['from_intent'])})" if c["from_intent"] else ""
            L.append(f"- **{c['label']}**, weight {c['weight']}{tag}")
            for ex in c["examples"]:
                L.append(f"  - \"{_q(ex['quote'], 240)}\" ({ex['source']})")
        L.append("")

    if r["read_first"]:
        L += ["## Read first (in this order)", ""]
        for i, p in enumerate(r["read_first"], 1):
            L.append(f"{i}. PEP {p['pep']}: {p['title']} ({p['why']})")
        L.append("")

    if r["people_to_engage"]:
        L += ["## People to engage", ""]
        for p in r["people_to_engage"]:
            roles = "; ".join(f"{ROLE_NAMES.get(k, k)} " + ", ".join(f"PEP {n}" for n in v) for k, v in p["roles"].items())
            L.append(f"- {p['name']} ({roles}; last active {p['last_active']})")
        L.append("")

    if r.get("where_to_discuss"):
        w = r["where_to_discuss"]
        L += ["## Where to discuss", "", f"{w['venue']}: {w['basis']}.", ""]

    t = r["area_track_record"]
    if t["peps"]:
        L += ["## Track record of this area", "",
              f"Concepts: {', '.join(t['concepts'])}. Of the {len(t['peps'])} PEPs focused on them: "
              f"{t['accepted']} accepted, {t['failed']} rejected/withdrawn, {t['open']} open.", "",
              ", ".join(f"PEP {p['pep']} ({p['status']})" for p in t["peps"]), ""]
    return "\n".join(L)


def explanation_md(r: dict) -> str:
    L = ["# How this came to be", "", f"> {_q(r['input']['text'], 300)}", "",
         f"Concepts: {', '.join(r['input']['concepts']) or '(none recognised)'}", "", "## Timeline", ""]
    for t in r["timeline"]:
        sup = f" → superseded by {', '.join('PEP %d' % s for s in t['superseded_by'])}" if t["superseded_by"] else ""
        L.append(f"- **{t['date'][:4] if t['date'] else '????'}: PEP {t['pep']}**, {t['title']} "
                 f"[{t['status']}, {t['relation'].lower()} {t['concept']}]{sup}")
        if t.get("decision") and t["decision"].get("rationale") and t["status"] in ("Rejected", "Withdrawn"):
            L.append(f"  - why it stopped: \"{_q(t['decision']['rationale'], 280)}\"")
    if r["turned_down"]:
        L += ["", "## Alternatives that were turned down along the way", ""]
        for i in r["turned_down"]:
            L.append(f"- **{i['idea']}** (PEP {i['pep']}, {i['year']})")
            if i.get("reason") or i.get("summary"):
                L.append(f"  - \"{_q(i.get('reason') or i.get('summary'))}\"")
            if i["revisited_by"]:
                L.append(f"  - ↻ revisited by {', '.join('PEP %d' % n for n in i['revisited_by'])}")
    return "\n".join(L) + "\n"
