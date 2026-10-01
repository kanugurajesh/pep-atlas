"""Central configuration: paths, the pinned data source, and the corpus definition."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw" / "peps"
KNOWLEDGE_DIR = ROOT / "knowledge"
GRAPH_PATH = KNOWLEDGE_DIR / "graph.json"
CACHE_DIR = ROOT / ".cache" / "peps"

PEPS_REPO = "https://github.com/python/peps"
# Pinned so the knowledge state is reproducible byte-for-byte.
PEPS_COMMIT = "f92659f44685d6ac9be4be6289ea9c8bba907466"

# Corpus = every PEP whose header says `Topic: Typing`, plus a short list of
# PEPs that are not tagged but are part of the typing story (the annotation
# syntax that typing grew out of, and typing proposals that were rejected or
# withdrawn before the Topic header existed). See approach.md section 1.
EXTRA_PEPS = {
    3107: "Function annotations: the syntax typing is built on",
    557: "Data classes: the target of dataclass_transform (PEP 681)",
    645: "Withdrawn `x?` optional syntax: a rejected typing proposal",
    712: "Rejected dataclass converter: interacts with dataclass_transform",
    637: "Rejected keyword indexing: motivated partly by typing use cases",
    661: "Sentinel values: carries a typing specification",
}
