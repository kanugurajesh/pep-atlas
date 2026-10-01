# Proposal assessment

> Let TypedDict items declare default values, so that a missing NotRequired key has a known value when read, and type checkers can treat d["key"] as always present.

## Verdict: Already exists  (confidence: high)

PEP 655 (Marking individual TypedDict items as required or potentially-missing, Final) covers this area and matches the proposal closely. Check that it addresses your specific mechanism; if it does not, it is the baseline your proposal extends.

## How the input was read

| Concept | Matched on | Specificity |
|---|---|---|
| Required / NotRequired keys | NotRequired | 0.41 |
| TypedDict | TypedDict | 0.28 |

Kind of change: checker semantics

## Closest prior PEPs

- **PEP 655: Marking individual TypedDict items as required or potentially-missing** (Final, 2021), score 0.858
  - why: extends TypedDict; introduces Required / NotRequired keys; shared wording: missing, item, typeddict, key, notrequired
- **PEP 589: TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys** (Final, 2019), score 0.526
  - why: introduces TypedDict; mentions Required / NotRequired keys; shared wording: key, typeddict, value, valu
- **PEP 728: TypedDict with Typed Extra Items** (Final, 2023), score 0.448
  - why: extends TypedDict; mentions Required / NotRequired keys; shared wording: item, typeddict, key, known, read
- **PEP 705: TypedDict: Read-only items** (Final, 2022), score 0.426
  - why: extends TypedDict; mentions Required / NotRequired keys; shared wording: read, typeddict, item
- **PEP 821: Support for unpacking TypedDicts in Callable type hints** (Draft, 2026), score 0.298
  - why: proposes TypedDict; mentions Required / NotRequired keys; shared wording: typeddict

## Similar ideas that were turned down

- **Marking required or potentially-missing keys with an operator** (PEP 655 § Rejected Ideas / Marking required or potentially-missing keys with an operator, 2021), score 0.563
  - stated reason: "It was decided that it would be prudent to introduce long-form notation (i.e."
  - concern types: Insufficient motivation / scope, Cost of new syntax
- **Special syntax around the key of a TypedDict item** (PEP 655 § Rejected Ideas / Special syntax around the *key* of a TypedDict item, 2021), score 0.548
  - stated reason: "This notation would require Python grammar changes and it is not believed that marking TypedDict items as required or potentially-missing would meet the high bar required to make such grammar changes. This notation causes Optional[] to take on different meanings depending on where it is positioned, which is…"
  - concern types: Ambiguity / inconsistency, Readability / teachability, Cost of new syntax
  - ↻ later revisited by **PEP 705** (TypedDict: Read-only items, Final)
- **Misalignment with how unions apply to values** (PEP 655 § Rejected Ideas / Marking absence of a value with a special constant / Misalignment with how unions apply to values, 2021), score 0.458
  - stated reason: "However this use of ...|Missing, equivalent to Union[..., Missing], doesn’t align well with what a union normally means: Union[...] always describes the type of a value that is present. By contrast missingness or non-totality is a property of a variable instead."
- **Support a New Syntax of Specifying Keys** (PEP 728 § Rejected Ideas / Support a New Syntax of Specifying Keys, 2023), score 0.448
  - stated reason: "While such users have a way to get around the issue, it's still a problem for them if they upgrade Python (or typing-extensions)."
  - concern types: Insufficient motivation / scope, Cost of new syntax
- **Support Extra Items with Intersection** (PEP 728 § Rejected Ideas / Support Extra Items with Intersection, 2023), score 0.448
  - context: "Supporting intersections in Python's type system requires a lot of careful consideration, and it can take a long time for the community to reach a consensus on a reasonable design."

## Objections to prepare for

- **Cost of new syntax**, weight 0.278
  - "Such operators could be implemented on type via the __pos__, __neg__ and __invert__ special methods without modifying the grammar." (PEP 655 (rejected idea: Marking required or potentially-missing keys with an operator))
  - "This notation would require Python grammar changes and it is not believed that marking TypedDict items as required or potentially-missing would meet the high bar required to make such grammar changes." (PEP 655 (rejected idea: Special syntax around the key of a TypedDict item))
- **Insufficient motivation / scope**, weight 0.18
  - "Future PEPs may reconsider introducing this or other short-form notation options." (PEP 655 (rejected idea: Marking required or potentially-missing keys with an operator))
  - "- The types don't appear in an annotation context, so their evaluation will not be deferred." (PEP 728 (rejected idea: Support a New Syntax of Specifying Keys))
- **Backward compatibility**, weight 0.178
  - "To retain backwards compatibility, type checkers should not infer a TypedDict type unless it is sufficiently clear that this is desired by the programmer." (PEP 589 (compat))
  - "Because extra_items is an opt-in feature, no existing codebase will break due to this change." (PEP 728 (compat))
- **Ambiguity / inconsistency**, weight 0.169 (typical for: checker semantics)
  - "This notation causes Optional[] to take on different meanings depending on where it is positioned, which is inconsistent and confusing." (PEP 655 (rejected idea: Special syntax around the key of a TypedDict item))
  - "* Because of generic functions, there will be plenty of cases where we can't evaluate a type operator (because it's applied to an unresolved type variable), and exactly what the type evaluation rules should be in those cases is somewhat…" (PEP 827 (open_issues))
- **Readability / teachability**, weight 0.098
  - "This notation causes Optional[] to take on different meanings depending on where it is positioned, which is inconsistent and confusing." (PEP 655 (rejected idea: Special syntax around the key of a TypedDict item))
- **Runtime behavior / introspection**, weight 0.045
  - "Tools that specifically rely on introspecting annotations at runtime (tools that parse Python files are obviously unaffected) that want to extract the annotations unevaluated and process them in some way are possibly in more trouble." (PEP 827 (compat))

## Read first (in this order)

1. PEP 484: Type Hints (foundation of PEP 589)
2. PEP 483: The Theory of Type Hints (foundation of PEP 589)
3. PEP 586: Literal Types (foundation of PEP 589)
4. PEP 591: Adding a final qualifier to typing (foundation of PEP 589)
5. PEP 589: TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys (closest prior proposal)
6. PEP 655: Marking individual TypedDict items as required or potentially-missing (closest prior proposal)
7. PEP 692: Using TypedDict for more precise **kwargs typing (foundation of PEP 728)
8. PEP 728: TypedDict with Typed Extra Items (closest prior proposal)

## People to engage

- Guido van Rossum (sponsor of PEP 589, PEP 655; decision delegate for PEP 589; last active 2021)
- David Foster (author of PEP 655; last active 2021)
- Jelle Zijlstra (sponsor of PEP 728, PEP 821; last active 2026)
- Zixuan James Li (author of PEP 728; last active 2023)
- Daniel Sperber (author of PEP 821; last active 2026)

## Where to discuss

discuss.python.org (Discourse): most recent related PEP (PEP 821, 2026) was discussed there.

## Track record of this area

Concepts: Required / NotRequired keys, TypedDict. Of the 8 PEPs focused on them: 5 accepted, 0 rejected/withdrawn, 3 open.

PEP 589 (Final), PEP 655 (Final), PEP 692 (Final), PEP 705 (Final), PEP 728 (Final), PEP 764 (Draft), PEP 821 (Draft), PEP 827 (Draft)

