"""A small, purpose-built reStructuredText reader for PEP files.

We only need three things from a PEP: the RFC 822 style header block, the
section tree (to know *where* a sentence lives: Rationale vs Rejected Ideas
matters a lot), and plain text per section. docutils would give a full doctree
but drags in rendering concerns and Sphinx-only roles (:pep:, :ref:) that it
cannot resolve outside the PEP build; a 100-line reader is easier to reason
about and to test.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ADORNMENT_CHARS = set("=-~^'\"*+#`:._")
ADORNMENT_RE = re.compile(r"^([=\-~^'\"*+#`:._])\1{2,}\s*$")


@dataclass
class Section:
    title: str
    level: int
    line: int
    own_text: str = ""
    children: list["Section"] = field(default_factory=list)
    parent: "Section | None" = field(default=None, repr=False)

    @property
    def path(self) -> list[str]:
        node, out = self, []
        while node is not None and node.level > 0:
            out.append(node.title)
            node = node.parent
        return out[::-1]

    def full_text(self) -> str:
        parts = [self.own_text]
        parts += [c.title + "\n" + c.full_text() for c in self.children]
        return "\n".join(p for p in parts if p)

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


@dataclass
class PepDocument:
    number: int
    headers: dict[str, str]
    root: Section
    raw: str

    def sections(self):
        """All sections except the synthetic root, in document order."""
        return [s for s in self.root.walk() if s.level > 0]

    def top_level(self, *names: str) -> Section | None:
        wanted = {n.lower() for n in names}
        for s in self.root.children:
            if s.title.lower() in wanted:
                return s
        return None


def parse_headers(lines: list[str]) -> tuple[dict[str, str], int]:
    headers: dict[str, str] = {}
    key = None
    i = 0
    for i, line in enumerate(lines):
        if not line.strip():
            break
        if line[0] in " \t" and key:
            headers[key] += " " + line.strip()
            continue
        m = re.match(r"^([A-Za-z-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            headers[key] = m.group(2).strip()
    return headers, i + 1


def _is_adornment(line: str, text: str) -> bool:
    return bool(ADORNMENT_RE.match(line)) and len(line.rstrip()) >= max(3, len(text.rstrip()) - 1)


def parse_sections(lines: list[str], offset: int) -> Section:
    """Detect RST titles (underline, optionally with overline). The heading
    level of a given adornment style is fixed by the order in which styles
    first appear in the document, which is how RST itself assigns levels."""
    root = Section(title="", level=0, line=0)
    styles: list[tuple[str, bool]] = []
    stack = [root]
    buf: list[str] = []
    i = 0
    n = len(lines)

    def flush():
        stack[-1].own_text = (stack[-1].own_text + "\n" + "\n".join(buf)).strip()
        buf.clear()

    while i < n:
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < n else ""
        heading = None
        # overline + title + underline
        if (ADORNMENT_RE.match(line) and i + 2 < n and lines[i + 1].strip()
                and lines[i + 2].rstrip() == line.rstrip() and not lines[i + 1].startswith(" ")):
            heading = (lines[i + 1].strip(), (line.strip()[0], True), 3)
        # title + underline
        elif (line.strip() and not line[0].isspace() and not ADORNMENT_RE.match(line)
              and _is_adornment(nxt, line) and (i == 0 or not lines[i - 1].strip())):
            heading = (line.strip(), (nxt.strip()[0], False), 2)

        if heading is None:
            buf.append(line)
            i += 1
            continue

        title, style, consumed = heading
        if style not in styles:
            styles.append(style)
        level = styles.index(style) + 1
        flush()
        while stack[-1].level >= level:
            stack.pop()
        sec = Section(title=title, level=level, line=offset + i + 1, parent=stack[-1])
        stack[-1].children.append(sec)
        stack.append(sec)
        i += consumed
    flush()
    return root


def load(path: Path) -> PepDocument:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    headers, body_start = parse_headers(lines)
    root = parse_sections(lines[body_start:], body_start)
    return PepDocument(number=int(headers["PEP"]), headers=headers, root=root, raw=raw)


# ---------------------------------------------------------------- text helpers

_ROLE_RE = re.compile(r":(?:pep|ref|py:\w+|class|func|data|attr|meth|mod|term|doc|rfc)?:`([^`]*)`")
_LINK_RE = re.compile(r"`([^`<]+?)\s*<[^>]+>`_+")


def plain(text: str) -> str:
    """Strip RST markup to readable prose (for evidence snippets and matching)."""
    text = re.sub(r"^\.\. [\w-]+::.*$", "", text, flags=re.MULTILINE)
    text = _LINK_RE.sub(r"\1", text)
    text = _ROLE_RE.sub(lambda m: re.sub(r"\s*<[^>]*>", "", m.group(1)), text)
    text = text.replace("``", "").replace("**", "")
    text = re.sub(r"(?<!\w)\*(\S[^*]*?)\*(?!\w)", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def paragraphs(text: str) -> list[str]:
    """Prose paragraphs only; indented literal/code blocks are dropped."""
    out = []
    for block in re.split(r"\n\s*\n", text):
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines or all(l.startswith((" ", "\t")) for l in lines) and not lines[0].lstrip().startswith(("*", "-", "#.")):
            continue
        if lines[0].startswith(">>>") or lines[0].rstrip().endswith("::") and len(lines) == 1:
            continue
        out.append(re.sub(r"\s+", " ", plain(" ".join(l.strip() for l in lines))).strip())
    return [p for p in out if len(p) > 20]


def first_sentences(text: str, max_chars: int = 320) -> str:
    paras = paragraphs(text)
    if not paras:
        return ""
    s = paras[0]
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars]
    end = max(cut.rfind(". "), cut.rfind("? "))
    return (cut[: end + 1] if end > 80 else cut.rstrip() + "…")
