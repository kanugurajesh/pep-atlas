"""Minimal TF-IDF + cosine index (pure Python).

Used as a *secondary* signal only: the primary retrieval path is through
concept nodes in the graph. Cosine keeps scores in [0, 1], which makes the
verdict thresholds in assess.py interpretable.
"""
from __future__ import annotations

import math
from collections import Counter

from .lexicon import tokenize


class TfidfIndex:
    def __init__(self, docs: dict[str, str]):
        self.ids = sorted(docs)
        tfs = {d: Counter(tokenize(docs[d])) for d in self.ids}
        df = Counter()
        for tf in tfs.values():
            df.update(tf.keys())
        n = len(self.ids)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
        self.vecs = {d: self._vec(tf) for d, tf in tfs.items()}

    def _vec(self, tf: Counter) -> dict[str, float]:
        v = {t: (1 + math.log(c)) * self.idf.get(t, 0.0) for t, c in tf.items() if t in self.idf}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def query_vec(self, text: str) -> dict[str, float]:
        return self._vec(Counter(tokenize(text)))

    def similarity(self, qvec: dict[str, float], doc_id: str) -> float:
        dv = self.vecs.get(doc_id, {})
        if len(qvec) > len(dv):
            qvec, dv = dv, qvec
        return sum(x * dv.get(t, 0.0) for t, x in qvec.items())

    def search(self, text: str, k: int | None = None) -> list[tuple[str, float]]:
        q = self.query_vec(text)
        scored = [(d, self.similarity(q, d)) for d in self.ids]
        scored = [s for s in scored if s[1] > 0]
        scored.sort(key=lambda s: (-s[1], s[0]))
        return scored[:k] if k else scored

    def shared_terms(self, text: str, doc_id: str, k: int = 6) -> list[str]:
        q = self.query_vec(text)
        dv = self.vecs.get(doc_id, {})
        common = sorted(((q[t] * dv[t], t) for t in q if t in dv), reverse=True)
        return [t for _, t in common[:k]]
