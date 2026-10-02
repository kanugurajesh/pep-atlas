"""Hand-curated vocabulary: the controlled set of things the knowledge base can
talk about, and the rules that recognize them in text.

Everything entity-like that is not given by a PEP header comes from here.
Nothing is learned or auto-extracted. Each entry is a deliberate modeling
decision, and the same lexicon is used both when building the graph and when
reading a new input. That shared vocabulary is what lets a new proposal "land"
on existing nodes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------- concepts


@dataclass(frozen=True)
class Concept:
    id: str
    label: str
    category: str
    description: str
    idents: tuple[str, ...] = ()        # code identifiers, case-sensitive
    phrases: tuple[str, ...] = ()       # prose regexes, case-insensitive
    strict: bool = False                # idents are also English words → need code context


def C(id, label, category, description, idents=(), phrases=(), strict=False):
    return Concept(id, label, category, description, tuple(idents), tuple(phrases), strict)


CATEGORIES = {
    "foundations": "Annotation syntax and the basic contract of type hints",
    "runtime": "How annotations exist and are evaluated at runtime",
    "generics": "Type parameters, variance and generic classes/functions",
    "structural": "Structural typing and dictionary/record shapes",
    "forms": "Special forms and type constructors in `typing`",
    "narrowing": "Type narrowing and refinement",
    "classes": "Class-level qualifiers, decorators and object model",
    "callables": "Typing functions and their signatures",
    "syntax": "New Python syntax introduced for typing",
    "ecosystem": "Distribution, tooling and governance of typing",
}

CONCEPTS: list[Concept] = [
    # foundations
    C("function_annotations", "Function annotations", "foundations",
      "The `def f(x: T) -> R` syntax that type hints are layered on.",
      phrases=[r"function annotations?", r"parameter annotations?"]),
    C("variable_annotations", "Variable annotations", "foundations",
      "Annotating variables and attributes with `x: T`.",
      phrases=[r"variable annotations?", r"annotated assignments?", r"attribute annotations?"]),
    C("gradual_typing", "Gradual typing / Any", "foundations",
      "Mixing typed and untyped code; the `Any` type.",
      idents=["Any"], phrases=[r"gradual typing", r"gradual guarantee", r"dynamic type"], strict=True),
    C("type_comments", "Type comments", "foundations",
      "`# type:` comments as an annotation channel for older Pythons.",
      phrases=[r"type comments?", r"# ?type:"]),
    C("stub_files", "Stub files", "ecosystem",
      "`.pyi` stubs and typeshed.",
      idents=["typeshed"], phrases=[r"stub files?", r"\.pyi\b", r"stubs? packages?"]),
    C("type_expressions", "Type expressions", "foundations",
      "The grammar of what may appear where a type is expected.",
      phrases=[r"type expressions?", r"annotation expressions?", r"valid type"]),
    # runtime
    C("annotations_runtime", "Runtime annotation access", "runtime",
      "`__annotations__`, `get_type_hints` and introspecting hints at runtime.",
      idents=["__annotations__", "get_type_hints", "get_annotations"],
      phrases=[r"runtime introspection", r"introspect\w*", r"at runtime"]),
    C("postponed_evaluation", "Postponed evaluation (stringified annotations)", "runtime",
      "`from __future__ import annotations`: annotations stored as strings.",
      phrases=[r"from __future__ import annotations", r"postponed evaluation", r"stringi[fz]ied annotations?",
               r"string annotations?"]),
    C("deferred_evaluation", "Deferred evaluation (lazy annotations)", "runtime",
      "Annotations computed lazily on access via `__annotate__` / annotationlib.",
      idents=["__annotate__", "annotationlib"], phrases=[r"deferred evaluation", r"lazy(ily)? evaluat\w+",
                                                         r"lazy annotations?"]),
    C("forward_references", "Forward references", "runtime",
      "Referring to names that are not defined yet in an annotation.",
      idents=["ForwardRef"], phrases=[r"forward references?", r"forward declarations?"]),
    C("type_checking_flag", "TYPE_CHECKING", "runtime",
      "The `TYPE_CHECKING` constant for checker-only imports.",
      idents=["TYPE_CHECKING"]),
    C("runtime_checking", "Runtime type enforcement", "runtime",
      "Checking or enforcing hints while the program runs.",
      idents=["runtime_checkable"],
      phrases=[r"runtime type[- ]check\w*", r"runtime (?:enforcement|validation)",
               r"enforc\w* (?:the )?(?:types?|type hints?|annotations?)",
               r"mandatory (?:type )?(?:hints|annotations)", r"type hints? (?:mandatory|required)",
               r"runtime[- ]checkable"]),
    C("class_getitem", "Generic class machinery (__class_getitem__)", "runtime",
      "Core hooks that make `C[int]` cheap at runtime.",
      idents=["__class_getitem__", "__mro_entries__"]),
    # generics
    C("typevar", "TypeVar", "generics", "Type variables for generic functions and classes.",
      idents=["TypeVar"], phrases=[r"type variables?"]),
    C("generic_classes", "Generic classes", "generics", "User-defined generic classes.",
      idents=["Generic"], phrases=[r"generic class(?:es)?", r"user-defined generics?", r"generic types?"], strict=True),
    C("variance", "Variance", "generics", "Covariance, contravariance, invariance of type parameters.",
      phrases=[r"covarian\w+", r"contravarian\w+", r"invarian\w+", r"\bvariance\b"]),
    C("bounds_constraints", "Bounds and constraints", "generics", "Upper bounds and value constraints on type variables.",
      phrases=[r"upper bounds?", r"bound=", r"constrained type var\w*", r"value restriction"]),
    C("paramspec", "ParamSpec", "generics", "Parameter specification variables for decorators.",
      idents=["ParamSpec", "Concatenate"], phrases=[r"parameter specification"]),
    C("variadic_generics", "Variadic generics (TypeVarTuple)", "generics", "Generics over an arbitrary number of types.",
      idents=["TypeVarTuple"], phrases=[r"variadic generics?", r"type variable tuples?", r"variadic"]),
    C("unpack", "Unpack", "generics", "`Unpack` / `*` unpacking in type expressions.",
      idents=["Unpack"], phrases=[r"unpack\w* (?:a |the )?typeddict", r"star[- ]unpack\w*"], strict=True),
    C("type_param_syntax", "Type parameter syntax", "syntax", "`def f[T]()` / `class C[T]` syntax.",
      phrases=[r"type parameter syntax", r"type parameter lists?", r"new syntax for (?:generic|type param)\w*",
               r"class \w+\[T", r"def \w+\[T"]),
    C("type_defaults", "Type parameter defaults", "generics", "Default values for type parameters.",
      phrases=[r"type (?:parameter |variable )?defaults?", r"defaults? for type (?:parameters|variables)"]),
    C("builtin_generics", "Builtin generic collections", "generics", "`list[int]` instead of `typing.List[int]`.",
      phrases=[r"standard collections?", r"built-?in (?:generics?|collections?)",
               r"(?-i:(?<![\w.])(?:list|dict|tuple|set|frozenset)\[)"]),
    C("type_aliases", "Type aliases", "generics", "Naming a type: `TypeAlias`, `type X = ...`.",
      idents=["TypeAlias", "TypeAliasType"], phrases=[r"type alias(?:es)?", r"type statement"]),
    # structural
    C("protocols", "Protocols (structural subtyping)", "structural", "Static duck typing via `Protocol`.",
      idents=["Protocol"], phrases=[r"structural subtyping", r"static duck typing", r"protocol classes?"], strict=True),
    C("typeddict", "TypedDict", "structural", "Dictionaries with a fixed set of typed keys.",
      idents=["TypedDict"], phrases=[r"typed dict(?:ionar(?:y|ies))?"]),
    C("required_keys", "Required / NotRequired keys", "structural", "Per-key totality in TypedDict.",
      idents=["NotRequired", "Required"], phrases=[r"\btotal=", r"totality", r"potentially[- ]missing"], strict=True),
    C("readonly", "Read-only items/attributes", "structural", "`ReadOnly` qualifier.",
      idents=["ReadOnly"], phrases=[r"read[- ]only (?:items?|attributes?|keys?)"]),
    C("extra_items", "Closed TypedDicts / extra items", "structural", "Typing keys beyond the declared ones.",
      idents=["extra_items"], phrases=[r"closed typeddicts?", r"extra items?", r"closed=True"]),
    C("inline_typeddict", "Inline TypedDict", "structural", "Anonymous TypedDict written inline.",
      phrases=[r"inline (?:\w+ )?typed ?dict\w*", r"anonymous typed ?dict\w*", r"typed ?dicts? inline"]),
    C("kwargs_typing", "Typing **kwargs", "callables", "Precise types for keyword arguments.",
      phrases=[r"\*\*kwargs", r"keyword arguments?"]),
    C("namedtuple", "NamedTuple", "structural", "Typed named tuples.", idents=["NamedTuple", "namedtuple"]),
    C("dataclasses", "Data classes", "classes", "`@dataclass` and dataclass-like libraries.",
      idents=["dataclass", "dataclasses"], phrases=[r"data ?classes?"]),
    C("dataclass_transform", "dataclass_transform", "classes", "Telling checkers a library behaves like dataclasses.",
      idents=["dataclass_transform"], phrases=[r"dataclass[- ]like"]),
    # forms
    C("union", "Union types", "forms", "`Union[X, Y]` and `Optional[X]`.",
      idents=["Union", "Optional"], phrases=[r"union types?", r"optional types?"], strict=True),
    C("union_operator", "`X | Y` union syntax", "syntax", "Writing unions with the `|` operator.",
      phrases=[r"``\w+ \| \w+``", r"\bX \| Y\b", r"``\|`` operator", r"__or__", r"pipe operator", r"\| None\b"]),
    C("optional_shorthand", "`X?` optional shorthand", "syntax", "Postfix `?` meaning Optional.",
      # Bare `T?` must be followed by more code or words: "Why not use tool X?" is a question, not syntax.
      phrases=[r"``\w+\?``", r"\b(?:int|str|T|X|x)\?(?=[ \t]*[\w\[\](),=:|])", r"``\?``", r"question mark",
               r"optional (?:type )?(?:operator|shorthand)"]),
    C("literal_types", "Literal types", "forms", "`Literal[...]` for specific values.",
      idents=["Literal"], phrases=[r"literal types?"], strict=True),
    C("literal_string", "LiteralString", "forms", "Strings that are known to be literal (injection safety).",
      idents=["LiteralString"], phrases=[r"literal strings?", r"injection attacks?"]),
    C("annotated", "Annotated", "forms", "Attaching metadata to types with `Annotated`.",
      idents=["Annotated"], phrases=[r"annotated metadata", r"metadata (?:in|on|for) (?:annotations|types)"], strict=True),
    C("callable_types", "Callable types", "callables", "`Callable[[A], R]` and callback typing.",
      idents=["Callable"], phrases=[r"callable types?", r"callback protocols?"], strict=True),
    C("callable_syntax", "Callable arrow syntax", "syntax", "`(int) -> str` as a type.",
      phrases=[r"callable (?:type )?syntax", r"arrow syntax", r"\(int\) -> \w+", r"shorthand (?:syntax )?for callable"]),
    C("self_type", "Self type", "forms", "`Self` for methods returning their own class.",
      idents=["Self"], phrases=[r"self type"], strict=True),
    C("never_noreturn", "Never / NoReturn", "forms", "The bottom type.",
      idents=["NoReturn", "Never"], phrases=[r"bottom type"], strict=True),
    C("newtype", "NewType", "forms", "Distinct nominal types with no runtime cost.", idents=["NewType"]),
    C("type_of_class", "type[C]", "forms", "The type of a class object.",
      phrases=[r"``[tT]ype\[\w+\]``", r"class objects?"]),
    C("typeform", "TypeForm", "forms", "Annotating values that are themselves type expressions.",
      idents=["TypeForm"], phrases=[r"type forms?"]),
    C("type_manipulation", "Type-level computation", "forms", "Computing types from types (mapped/conditional types).",
      phrases=[r"type manipulation", r"conditional types?", r"mapped types?", r"type[- ]level (?:computation|programming|operators?)"]),
    C("overload", "Overloads", "callables", "`@overload` for multiple signatures.", idents=["overload"],
      phrases=[r"(?:function|method)(?:/method)? overloading", r"overloaded (?:functions?|signatures?)"]),
    C("explicit_specialization", "Subscriptable functions", "callables", "Explicitly specializing generic functions `f[int]`.",
      phrases=[r"subscriptable functions?", r"explicit(?:ly)? speciali[sz]\w+"]),
    C("keyword_indexing", "Keyword arguments in indexing", "syntax", "`a[x, key=1]` subscription syntax.",
      phrases=[r"indexing with keyword", r"keyword (?:arguments? )?(?:in|for) (?:indexing|subscript\w*)", r"keyword subscript\w*"]),
    # narrowing
    C("narrowing", "Type narrowing", "narrowing", "Refining a variable's type through control flow.",
      phrases=[r"narrow\w*", r"type refinement"]),
    C("typeguard", "TypeGuard", "narrowing", "User-defined type guard functions.",
      idents=["TypeGuard"], phrases=[r"type guards?", r"user-defined type guards?"]),
    C("typeis", "TypeIs", "narrowing", "Bidirectional user-defined narrowing.", idents=["TypeIs"]),
    # classes
    C("final", "Final", "classes", "`Final` names and `@final` classes/methods.",
      idents=["Final", "final"], phrases=[r"final qualifier"], strict=True),
    C("classvar", "ClassVar", "classes", "Marking class-level attributes.", idents=["ClassVar"]),
    C("override", "@override", "classes", "Explicitly marking method overrides.",
      idents=["override"], phrases=[r"method overrid\w+"], strict=True),
    C("deprecated", "@deprecated", "classes", "Deprecation surfaced through the type system.",
      idents=["deprecated"], phrases=[r"deprecat\w+"], strict=True),
    C("disjoint_bases", "Disjoint bases", "classes", "Classes that cannot share a subclass.",
      idents=["disjoint_base"], phrases=[r"disjoint bases?", r"solid bases?"]),
    C("buffer_protocol", "Buffer protocol", "classes", "`__buffer__` and `collections.abc.Buffer`.",
      idents=["__buffer__", "Buffer"], phrases=[r"buffer protocol"], strict=True),
    C("sentinels", "Sentinel values", "classes", "Unique marker objects and how to type them.",
      phrases=[r"sentinels?"]),
    C("docs_in_types", "Documentation in types", "ecosystem", "Docstrings/`Doc()` attached to annotations or aliases.",
      idents=["Doc"], phrases=[r"docstrings? for", r"documentation (?:in|of) (?:annotat\w+|parameters|type aliases)"], strict=True),
    # ecosystem
    C("packaging_types", "Distributing type information", "ecosystem", "`py.typed`, stub-only packages.",
      phrases=[r"py\.typed", r"stub-only packages?", r"distribut\w+ type information"]),
    C("typing_governance", "Typing governance", "ecosystem", "Typing Council, the typing spec and conformance.",
      phrases=[r"typing council", r"typing governance", r"typing spec(?:ification)?", r"conformance"]),
]

CONCEPT_BY_ID = {c.id: c for c in CONCEPTS}

# Type checkers and related tools. A separate entity type because "where was
# this implemented" is a different question from "what is it about".
TOOLS = {
    "mypy": r"\bmypy\b", "pyright": r"\bpyright\b", "pyre": r"\bpyre\b", "pytype": r"\bpytype\b",
    "pyanalyze": r"\bpyanalyze\b", "typeshed": r"\btypeshed\b", "typing_extensions": r"\btyping[_-]extensions\b",
    "pyrefly": r"\bpyrefly\b", "ty": r"\bty\b(?= (?:type )?checker)", "basedpyright": r"\bbasedpyright\b",
}


def _ident_pattern(ident: str, strict: bool) -> re.Pattern:
    e = re.escape(ident)
    if not strict:
        return re.compile(rf"(?<![\w.]){e}(?!\w)|typing\.{e}(?!\w)")
    # Ambiguous identifiers (Final, Self, Any, ...) only count in code context.
    return re.compile(
        rf"``[^`\n]*(?<![\w]){e}(?!\w)[^`\n]*``"   # inside an inline literal
        rf"|(?:typing(?:_extensions)?\.|@){e}(?!\w)"  # qualified or decorator
        rf"|(?<![\w.]){e}\["                          # subscripted
        rf"|(?:->|:)\s*{e}(?!\w)"                      # in an annotation position
    )


_CORPUS_PATTERNS = {
    c.id: ([_ident_pattern(i, c.strict) for i in c.idents],
           [re.compile(p, re.IGNORECASE) for p in c.phrases])
    for c in CONCEPTS
}

_HEADING_PATTERNS = {
    c.id: ([_ident_pattern(i, strict=False) for i in c.idents],
           [re.compile(p, re.IGNORECASE) for p in c.phrases])
    for c in CONCEPTS
}


def concepts_in_heading(title: str) -> set[str]:
    """Section headings are short and deliberate: a bare ``Callable`` heading
    means the construct, so identifiers match without code context."""
    t = re.sub(r"[`*]", "", title)
    return {cid for cid, (idents, phrases) in _HEADING_PATTERNS.items()
            if any(p.search(t) for p in idents + phrases)}


_AMBIGUOUS_IN_INPUT = {"Any", "Final", "Self", "Never", "Required", "Union", "Optional", "List", "Dict", "Doc",
                       "Buffer", "Generic", "Protocol", "Literal", "Callable", "Annotated", "Unpack"}


def _input_ident_pattern(ident: str) -> re.Pattern:
    e = re.escape(ident)
    if ident in _AMBIGUOUS_IN_INPUT:
        # In free text, a capitalized word at sentence start is not a type.
        return re.compile(rf"(?<![.!?]\s)(?<!^)(?<![\w.]){e}(?!\w)|`{e}|typing\.{e}|{e}\[|@{e}\b")
    return re.compile(rf"(?<![\w.]){e}(?!\w)|typing\.{e}(?!\w)", 0 if ident[0].isupper() or "_" in ident else re.IGNORECASE)


_INPUT_PATTERNS = {
    c.id: ([_input_ident_pattern(i) for i in c.idents],
           [re.compile(p, re.IGNORECASE) for p in c.phrases])
    for c in CONCEPTS
}


_ROLE_TO_TEXT = re.compile(r":[\w:]+:`([^`<]*?)\s*(?:<[^>]*>)?`")


def count_concepts(raw_rst: str) -> dict[str, int]:
    """Concept mention counts in a piece of PEP text (corpus side). Phrases are
    matched on whitespace-normalized RST with roles resolved but ``literals``
    kept, so a phrase pattern may require code markup where prose would be
    ambiguous."""
    norm = _ROLE_TO_TEXT.sub(r"\1", re.sub(r"\s+", " ", raw_rst)).replace("\\*", "*")
    out = {}
    for cid, (idents, phrases) in _CORPUS_PATTERNS.items():
        n = sum(len(p.findall(raw_rst)) for p in idents) + sum(len(p.findall(norm)) for p in phrases)
        if n:
            out[cid] = n
    return out


def match_input(text: str) -> dict[str, list[str]]:
    """Concepts in free-form user text, with the surface forms that triggered them."""
    out: dict[str, list[str]] = {}
    for cid, (idents, phrases) in _INPUT_PATTERNS.items():
        hits = [m.group(0).strip("`@[ ") for p in idents + phrases for m in p.finditer(text)]
        if hits:
            out[cid] = sorted(set(hits))
    return out


def find_tools(text: str) -> dict[str, int]:
    out = {}
    for tool, pat in TOOLS.items():
        n = len(re.findall(pat, text, re.IGNORECASE))
        if n:
            out[tool] = n
    return out


# --------------------------------------------------------------------- concerns
# The recurring *kinds* of objection raised against typing proposals. Each rule
# is a list of cue regexes; a paragraph that hits a cue is evidence for the
# concern. Concern nodes are what turn "these ideas were rejected" into "here
# is what reviewers will ask you".

CONCERNS = {
    "backward_compat": ("Backward compatibility",
                        [r"backwards?[- ]compat\w*", r"break(?:s|ing)? (?:existing|backward|user|code)",
                         r"existing code", r"breaking change"]),
    "runtime_cost": ("Runtime cost",
                     [r"(?:runtime|import[- ]time|startup) (?:cost|overhead|performance|penalty)",
                      r"\bperformance\b", r"\bslow(?:er|down)?\b", r"memory (?:usage|overhead|cost)"]),
    "syntax_cost": ("Cost of new syntax",
                    [r"new syntax", r"grammar change", r"\bgrammar\b", r"syntax change", r"\bparser\b",
                     r"soft keyword", r"new keyword", r"syntactic(?:ally)?"]),
    "checker_complexity": ("Burden on type checkers",
                           [r"(?:hard|difficult|complex) (?:for type checkers|to implement)",
                            r"type checkers? (?:would|will) (?:need|have) to", r"implementation complexity",
                            r"complicat\w+ (?:the )?(?:type )?checkers?"]),
    "readability": ("Readability / teachability",
                    [r"confus\w+", r"readab\w+", r"\bteach\w*", r"\blearn\w*", r"(?:un)?intuitive", r"surpris\w+",
                     r"\bugly\b", r"\bverbose\b", r"cognitive"]),
    "ambiguity": ("Ambiguity / inconsistency",
                  [r"ambigu\w+", r"inconsisten\w+", r"\bunclear\b", r"edge cases?", r"corner cases?"]),
    "soundness": ("Type safety / soundness",
                  [r"\bunsound\w*", r"\bsoundness\b", r"type[- ]safe\w*", r"false (?:positives|negatives)"]),
    "insufficient_motivation": ("Insufficient motivation / scope",
                                [r"\buse cases? (?:is|are) (?:rare|uncommon|not)", r"not (?:common|compelling|worth)",
                                 r"out of scope", r"(?:future|separate|later|follow-up) PEP", r"could be added later",
                                 r"\bYAGNI\b", r"\bdefer\w*", r"not enough (?:demand|motivation|use)"]),
    "runtime_semantics": ("Runtime behavior / introspection",
                          [r"\bat runtime\b", r"\bintrospect\w*", r"__annotations__", r"get_type_hints",
                           r"\bisinstance\b"]),
    "ecosystem_impact": ("Impact on libraries and tools",
                         [r"third[- ]party", r"library (?:authors|maintainers)", r"existing (?:tools|libraries)",
                          r"\btypeshed\b", r"\bIDEs?\b"]),
}

_CONCERN_RE = {k: [re.compile(p, re.IGNORECASE) for p in pats] for k, (_, pats) in CONCERNS.items()}


def classify_concerns(paragraph_list: list[str]) -> dict[str, str]:
    """concern_id -> the best evidence sentence (first sentence carrying a cue)."""
    out: dict[str, str] = {}
    for para in paragraph_list:
        for sent in split_sentences(para):
            for cid, pats in _CONCERN_RE.items():
                if cid not in out and any(p.search(sent) for p in pats):
                    out[cid] = sent
    return out


# --------------------------------------------------------- section semantics
# Where a sentence lives changes what it means. A PEP reference in a
# "Rejected Ideas" section is a contrast; in "Motivation" it is a foundation.

SECTION_KINDS = [
    ("decision", r"^(?:resolution|acceptance|rejection notice|pep withdrawal|withdrawal|status|notice for reviewers|pep status)"),
    ("rejected", r"reject|alternative|why not|other proposals|discarded|postponed (?:ideas|proposals)|objection|rejected names"
                 r"|^non-?goals?$|out of scope"),
    ("abstract", r"^abstract$|^summary$"),
    ("motivation", r"motivation|rationale|background|introduction|overview|goals"),
    ("specification", r"specification|proposal|semantics|syntax|definition|grammar|runtime|implementation details|binding rules"),
    ("compat", r"backwards? compat|backward-compat"),
    ("reference_impl", r"reference implementation|implementation$"),
    ("open_issues", r"open issues|open questions|unresolved"),
    ("teaching", r"how to teach"),
    ("security", r"security"),
    ("meta", r"^(?:copyright|acknowledg\w*|references|footnotes|change ?log|resources|appendix.*)$"),
]
_SECTION_KIND_RE = [(k, re.compile(p, re.IGNORECASE)) for k, p in SECTION_KINDS]


def section_kind(path: list[str]) -> str:
    """Classify by the nearest ancestor title that matches a rule."""
    for title in reversed(path):
        t = re.sub(r"[`*]", "", title).strip()
        for kind, pat in _SECTION_KIND_RE:
            if pat.search(t):
                return kind
    return "body"


REJECTED_HEADING_RE = re.compile(
    r"reject|^alternatives?\b|alternatives? considered|^why not|other proposals|discarded|postponed (?:ideas|proposals)"
    r"|^non-?goals?$|out of scope",
    re.IGNORECASE)

REASON_CUES = re.compile(
    r"\b(?:reject\w*|decided|because|problem|downside|drawback|disadvantage|however|instead|unfortunately|"
    r"would (?:require|break|make|be)|not (?:worth|clear|possible|feasible|designed|intended|a goal)|confus\w+|too|"
    r"no (?:desire|intent\w*|plans?)|never|will remain)\b",
    re.IGNORECASE)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z`(\"'])", text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


# ------------------------------------------------------------- input intents
# What kind of change a new proposal is. Used to pull the concerns that were
# historically raised against the same kind of change.

INTENTS = {
    "new_syntax": [r"\bsyntax\b", r"\boperator\b", r"\bkeyword\b", r"\bgrammar\b", r"shorthand", r"\bnew notation\b"],
    "new_special_form": [r"special form", r"new type (?:construct|qualifier|form)", r"add \w+ to (?:the )?typing",
                         r"typing\.\w+", r"\bqualifier\b", r"\bdecorator\b"],
    "runtime_change": [r"\bruntime\b", r"\bat run ?time\b", r"\bisinstance\b", r"\bintrospect\w*", r"__annotations__",
                       r"\benforce\w*", r"\bvalidat\w+"],
    "checker_semantics": [r"type checkers?", r"\binfer\w*", r"\bnarrow\w*", r"\bsubtyp\w+", r"\bassignab\w+",
                          r"\berror\b"],
    "stdlib_change": [r"standard library", r"\bstdlib\b", r"\bbuiltins?\b", r"collections\.abc"],
}
_INTENT_RE = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in INTENTS.items()}

# Which concerns each kind of change historically attracts (a modeling prior,
# refined at query time by what the graph actually contains).
INTENT_CONCERNS = {
    "new_syntax": ["syntax_cost", "readability", "backward_compat"],
    "new_special_form": ["insufficient_motivation", "readability", "checker_complexity"],
    "runtime_change": ["runtime_cost", "runtime_semantics", "backward_compat"],
    "checker_semantics": ["soundness", "checker_complexity", "ambiguity"],
    "stdlib_change": ["backward_compat", "ecosystem_impact"],
}


def detect_intents(text: str) -> list[str]:
    return [k for k, pats in _INTENT_RE.items() if any(p.search(text) for p in pats)]


# ---------------------------------------------------------------- tokenizing
STOPWORDS = set("""a an the and or of to in for on with by is are was were be been being this that these those it its
as at from but not no can could would should will may might must which who whom what when where how than then there
their they them we our you your i he she his her also such into if so do does did have has had more most other some any
all each only same new use used using via e g eg i e ie pep peps python type types typing proposal propose proposed
""".split())


def tokenize(text: str) -> list[str]:
    toks = re.findall(r"[a-z_][a-z0-9_]+", text.lower())
    out = []
    for t in toks:
        t = t.strip("_")
        if len(t) < 3 or t in STOPWORDS:
            continue
        for suf in ("ies", "es", "s"):
            if t.endswith(suf) and len(t) > len(suf) + 3 and not t.endswith("ss"):
                t = t[: -len(suf)] + ("y" if suf == "ies" else "")
                break
        out.append(t)
    return out
