"""Self-contained HTML viewer for the knowledge graph (vis-network from a CDN,
data embedded). Open knowledge/graph.html in a browser; no server needed."""
from __future__ import annotations

import json
from pathlib import Path

from .graph import KnowledgeGraph

COLORS = {"PEP": "#3b6ea8", "Concept": "#2f9e6e", "RejectedIdea": "#c0563b", "Person": "#8a63b8",
          "Concern": "#d08a1e", "Decision": "#6b6b6b", "PythonVersion": "#9aa5b1", "Venue": "#9aa5b1",
          "Tool": "#4f9aa8"}

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PEP Atlas graph</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
 body{margin:0;font:14px system-ui,sans-serif;display:flex;height:100vh;color:#1d2228}
 #side{width:380px;overflow:auto;padding:12px 14px;border-right:1px solid #ddd;background:#fafafa}
 #net{flex:1}
 h1{font-size:17px;margin:4px 0 8px} h2{font-size:14px;margin:14px 0 4px}
 label{display:inline-block;margin:2px 8px 2px 0;font-size:13px}
 .sw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px}
 input[type=search]{width:100%;padding:6px;box-sizing:border-box;margin:6px 0}
 .e{font-size:12px;margin:3px 0;padding:3px 0;border-bottom:1px solid #eee}
 .t{font-weight:600;color:#555} .ev{color:#666;font-style:italic} a{color:#3b6ea8;cursor:pointer}
 pre{white-space:pre-wrap;font-size:12px;background:#fff;border:1px solid #eee;padding:6px}
</style></head><body>
<div id="side">
 <h1>PEP Atlas: typing knowledge graph</h1>
 <div>Showing node types (edges among the shown nodes are drawn):</div>
 <div id="filters"></div>
 <input id="q" type="search" placeholder="Find a node (e.g. 604, TypedDict, Guido)">
 <div id="info">Click a node to see its attributes and every edge with its provenance.</div>
</div>
<div id="net"></div>
<script>
const DATA = __DATA__;
const COLORS = __COLORS__;
const DEFAULT_ON = new Set(["PEP","Concept","RejectedIdea"]);
const byId = Object.fromEntries(DATA.nodes.map(n => [n.id, n]));
const label = n => n.type==="PEP" ? `PEP ${n.number}` : (n.label||n.name||n.title||n.id);
const filters = document.getElementById("filters");
Object.keys(COLORS).forEach(t => {
  const l = document.createElement("label");
  l.innerHTML = `<input type=checkbox value="${t}" ${DEFAULT_ON.has(t)?"checked":""}> <span class=sw style="background:${COLORS[t]}"></span>${t}`;
  filters.appendChild(l);
});
let network;
function draw(){
  const on = new Set([...filters.querySelectorAll("input:checked")].map(i=>i.value));
  const nodes = DATA.nodes.filter(n => on.has(n.type) && !(n.type==="PEP" && !n.in_corpus)).map(n => ({
    id:n.id, label:label(n), title:(n.title||n.label||n.name||""), color:COLORS[n.type],
    shape: n.type==="PEP" ? "dot" : (n.type==="RejectedIdea" ? "triangle" : "diamond"),
    size: n.type==="PEP" ? 14 : (n.type==="RejectedIdea" ? 6 : 10), font:{size: n.type==="RejectedIdea"?0:12}}));
  const ids = new Set(nodes.map(n=>n.id));
  const edges = DATA.edges.filter(e => ids.has(e.src) && ids.has(e.dst) && e.type!=="MENTIONS").map((e,i) => ({
    id:i, from:e.src, to:e.dst, arrows:"to", color:{opacity:0.35}, title:e.type,
    dashes: e.type==="REVISITED_BY" || e.type==="CONTRASTS_WITH"}));
  network = new vis.Network(document.getElementById("net"), {nodes, edges},
    {physics:{solver:"forceAtlas2Based", stabilization:{iterations:150}}, interaction:{hover:true}});
  network.on("click", p => p.nodes.length && show(p.nodes[0]));
}
function esc(s){return String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))}
function show(id){
  const n = byId[id]; if(!n) return;
  const attrs = Object.assign({}, n); delete attrs.text;
  const out = DATA.edges.filter(e=>e.src===id), inc = DATA.edges.filter(e=>e.dst===id);
  const row = (e, other, dir) => `<div class=e><span class=t>${dir}${e.type}</span> <a onclick="show('${other}')">${esc(label(byId[other]||{id:other}))}</a>
     ${e.section?`<br><span>§ ${esc(e.section)}</span>`:""}${e.evidence?`<br><span class=ev>“${esc(e.evidence)}”</span>`:""}
     <br><span style="color:#999">confidence ${e.confidence} · source ${esc(e.source)}</span></div>`;
  document.getElementById("info").innerHTML = `<h2>${esc(n.type)}: ${esc(label(n))}</h2><pre>${esc(JSON.stringify(attrs,null,1))}</pre>
    <h2>Outgoing (${out.length})</h2>${out.map(e=>row(e,e.dst,"→ ")).join("")}
    <h2>Incoming (${inc.length})</h2>${inc.map(e=>row(e,e.src,"← ")).join("")}`;
  if (network && network.body.data.nodes.get(id)) { network.selectNodes([id]); network.focus(id,{scale:1.1,animation:true}); }
}
filters.addEventListener("change", draw);
document.getElementById("q").addEventListener("change", ev => {
  const q = ev.target.value.toLowerCase().trim();
  const hit = DATA.nodes.find(n => String(n.number)===q || label(n).toLowerCase().includes(q) || (n.title||"").toLowerCase().includes(q));
  if (hit) show(hit.id);
});
draw();
</script></body></html>
"""


def write_viewer(g: KnowledgeGraph, path: Path):
    data = g.to_json()
    slim = {"nodes": data["nodes"], "edges": data["edges"]}
    html = TEMPLATE.replace("__DATA__", json.dumps(slim, ensure_ascii=False).replace("</", "<\\/")) \
                   .replace("__COLORS__", json.dumps(COLORS))
    path.write_text(html, encoding="utf-8")
