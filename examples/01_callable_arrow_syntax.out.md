# Proposal assessment

> I'd like to propose a shorthand syntax for callable types: write (int, str) -> bool instead of Callable[[int, str], bool]. The nested brackets are hard to read, especially for higher-order functions and decorators.

## Verdict: Previously rejected  (confidence: high)

PEP 677 (Callable Type Syntax) proposed this and was rejected. A new attempt has to answer the reasons recorded in its decision.

## How the input was read

| Concept | Matched on | Specificity |
|---|---|---|
| Callable arrow syntax | shorthand syntax for callable | 0.55 |
| Callable types | Callable, callable types | 0.31 |

Kind of change: new syntax

## Closest prior PEPs

- **PEP 677: Callable Type Syntax** (Rejected, 2021), score 0.955
  - why: proposes Callable types; proposes Callable arrow syntax; shared wording: callable, bool, int, str, syntax
  - decision rationale is not in the PEP text; see the resolution: https://mail.python.org/archives/list/python-dev@python.org/message/NHCLHCU2XCWTBGF732WESMN42YYVKOXB/
- **PEP 612: Parameter Specification Variables** (Final, 2019), score 0.428
  - why: extends Callable types; shared wording: callable, bool, int, str, decorator
- **PEP 821: Support for unpacking TypedDicts in Callable type hints** (Draft, 2026), score 0.305
  - why: proposes Callable types; shared wording: callable, function
- **PEP 484: Type Hints** (Final, 2014), score 0.273
  - why: introduces Callable types; shared wording: callable, bracket, syntax, function
- **PEP 827: Type Manipulation** (Draft, 2026), score 0.256
  - why: proposes Callable types; shared wording: callable, like, syntax, decorator, function

## Similar ideas that were turned down

- **Requiring Outer Parentheses** (PEP 677 § Rejected Alternatives / Other Proposals Considered / Requiring Outer Parentheses, 2021), score 0.758
  - stated reason: "This makes the nesting of many examples that are difficult to follow clear, but we rejected it because We rejected this change because: - The outer parentheses only help readability in some cases, mostly when a callable type is used in return position."
  - concern types: Readability / teachability, Cost of new syntax
- **Hybrid keyword-arrow Syntax** (PEP 677 § Rejected Alternatives / Other Proposals Considered / Hybrid keyword-arrow Syntax, 2021), score 0.73
  - stated reason: "But we think this might confuse readers into thinking def(A, B) -> C is a lambda, particularly because Javascript's function keyword is used in both named and anonymous functions."
  - concern types: Readability / teachability
- **Making -> bind tighter than |** (PEP 677 § Rejected Alternatives / Other Proposals Considered / Making ``->`` bind tighter than ``|``, 2021), score 0.67
  - stated reason: "We considered having -> bind tighter so that instead the expression would parse as ((int, str) -> bool) | None. - It means we no would longer have to treat None | (int, str) -> bool as a syntax error. - Looking at typeshed today, optional callable arguments are very common because using None as a default value is a…"
  - concern types: Impact on libraries and tools, Readability / teachability
- **Improving Usability of the Indexed Callable Type** (PEP 677 § Rejected Alternatives / Other Proposals Considered / Improving Usability of the Indexed Callable Type, 2021), score 0.595
  - stated reason: "One proposal would be to make the builtin callable function indexable so that it could be used as a type:: This change would be analogous to 585 that made built in collections like list and dict usable as types, and would make imports more convenient, but it wouldn't help readability of the types themselves much. In…"
  - concern types: Readability / teachability, Cost of new syntax
- **Using the plain return type in __args__ for async types** (PEP 677 § Rejected Alternatives / Alternative Runtime Behaviors / Using the plain return type in ``__args__`` for async types, 2021), score 0.44
  - stated reason: "The reason is that one could argue they are not expressible directly using typing.Callable, and therefore it would be fine to set __args__ as (int, int) rather than (int, typing.Awaitable[int]). But we believe this would be problematic."
  - concern types: Backward compatibility

## Objections to prepare for

- **Readability / teachability**, weight 0.375 (typical for: new syntax)
  - "A concern with the current proposal is readability, particularly when callable types are used in return type position which leads to multiple top-level -> tokens, for example::" (PEP 677 (rejected idea: Requiring Outer Parentheses))
  - "But we think this might confuse readers into thinking def(A, B) -> C is a lambda, particularly because Javascript's function keyword is used in both named and anonymous functions." (PEP 677 (rejected idea: Hybrid keyword-arrow Syntax))
- **Backward compatibility**, weight 0.248 (typical for: new syntax)
  - "It is debatable whether we are required to preserve backward compatibility of __args__ for async callable types like async (int) -> str." (PEP 677 (rejected idea: Using the plain return type in __args__ for async types))
  - "We do want stub files, but they are primarily useful for adding type hints to existing code that doesn't lend itself to adding type hints, e.g. 3rd party packages, code that needs to support both Python 2 and Python 3, and especially…" (PEP 484 (compat))
- **Cost of new syntax**, weight 0.208 (typical for: new syntax)
  - "- We believe it is more appropriate to encourage this in style guides, linters, and autoformatters than to bake it into the parser and throw syntax errors. - Moreover, if a type is complicated enough that readability is a concern we can…" (PEP 677 (rejected idea: Requiring Outer Parentheses))
  - "If we do not want to add new syntax for callable types, we could look at how to make the existing type easier to read." (PEP 677 (rejected idea: Improving Usability of the Indexed Callable Type))
- **Impact on libraries and tools**, weight 0.08
  - "- It means we no would longer have to treat None | (int, str) -> bool as a syntax error. - Looking at typeshed today, optional callable arguments are very common because using None as a default value is a standard Python idiom." (PEP 677 (rejected idea: Making -> bind tighter than |))
- **Runtime behavior / introspection**, weight 0.059
  - "There is no particular interaction between this proposal and from __future__ import annotations - just like any other type annotation it will be unparsed to a string at module import, and typing.get_type_hints should correctly evaluate…" (PEP 677 (compat))
  - "Tools that specifically rely on introspecting annotations at runtime (tools that parse Python files are obviously unaffected) that want to extract the annotations unevaluated and process them in some way are possibly in more trouble." (PEP 827 (compat))

## Read first (in this order)

1. PEP 484: Type Hints (foundation of PEP 612)
2. PEP 483: The Theory of Type Hints (foundation of PEP 544 → PEP 612)
3. PEP 544: Protocols: Structural subtyping (static duck typing) (foundation of PEP 612)
4. PEP 612: Parameter Specification Variables (closest prior proposal)
5. PEP 677: Callable Type Syntax (closest prior proposal (read why it failed))
6. PEP 821: Support for unpacking TypedDicts in Callable type hints (closest prior proposal)

## People to engage

- Guido van Rossum (sponsor of PEP 612, PEP 677; decision delegate for PEP 612; author of PEP 484; last active 2021)
- Pradeep Kumar Srinivasan (author of PEP 677; last active 2021)
- Steven Troxler (author of PEP 677; last active 2021)
- Daniel Sperber (author of PEP 821; last active 2026)
- Daniel W. Park (author of PEP 827; last active 2026)

## Where to discuss

discuss.python.org (Discourse): most recent related PEP (PEP 821, 2026) was discussed there.

## Track record of this area

Concepts: Callable arrow syntax, Callable types. Of the 5 PEPs focused on them: 2 accepted, 1 rejected/withdrawn, 2 open.

PEP 484 (Final), PEP 612 (Final), PEP 677 (Rejected), PEP 821 (Draft), PEP 827 (Draft)

