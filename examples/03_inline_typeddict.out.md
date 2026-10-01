# Proposal assessment

> Add a way to write a TypedDict inline in an annotation without declaring a class first, e.g. def get_user() -> {"name": str, "age": int}: ...

## Verdict: Already in progress  (confidence: high)

PEP 764 (Inline typed dictionaries) is an open draft on this topic; contributing to it is likely more effective than a competing PEP.

## How the input was read

| Concept | Matched on | Specificity |
|---|---|---|
| Inline TypedDict | TypedDict inline | 0.55 |
| TypedDict | TypedDict | 0.28 |

## Closest prior PEPs

- **PEP 764: Inline typed dictionaries** (Draft, 2024), score 0.791
  - why: proposes TypedDict; proposes Inline TypedDict; shared wording: inline, add, class, annotation
- **PEP 728: TypedDict with Typed Extra Items** (Final, 2023), score 0.314
  - why: extends TypedDict; shared wording: typeddict, str, without, class
- **PEP 589: TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys** (Final, 2019), score 0.273
  - why: introduces TypedDict; shared wording: typeddict, class
- **PEP 692: Using TypedDict for more precise **kwargs typing** (Final, 2022), score 0.268
  - why: extends TypedDict; shared wording: typeddict, way, annotation
- **PEP 821: Support for unpacking TypedDicts in Callable type hints** (Draft, 2026), score 0.261
  - why: proposes TypedDict; shared wording: typeddict

## Similar ideas that were turned down

- **Support a New Syntax of Specifying Keys** (PEP 728 § Rejected Ideas / Support a New Syntax of Specifying Keys, 2023), score 0.316
  - stated reason: "While such users have a way to get around the issue, it's still a problem for them if they upgrade Python (or typing-extensions)."
  - concern types: Insufficient motivation / scope, Cost of new syntax
- **Change Optional to mean “optional item” in certain contexts instead of “nullable”** (PEP 655 § Rejected Ideas / Change Optional to mean “optional item” in certain contexts instead of “nullable”, 2021), score 0.299
  - stated reason: "This would add more confusion for users because it would mean that in some contexts the meaning of Optional[] is different than in other contexts, and it would be easy to overlook the flag."
  - concern types: Readability / teachability
  - ↻ later revisited by **PEP 705** (TypedDict: Read-only items, Final)
- **Rejected Alternatives (PEP 589)** (PEP 589 § Rejected Alternatives, 2019), score 0.295
  - stated reason: "Several proposed ideas were rejected. The current set of features seem to cover a lot of ground, and it was not clear which of the proposed extensions would be more than marginally useful."
  - concern types: Impact on libraries and tools, Runtime behavior / introspection
  - ↻ later revisited by **PEP 655** (Marking individual TypedDict items as required or potentially-missing, Final)
- **Using dict or typing.Dict with a single type argument** (PEP 764 § Rejected Ideas / Using ``dict`` or ``typing.Dict`` with a single type argument, 2024), score 0.292
  - stated reason: "Allowing dict to be parametrized with a single type argument would require special casing from type checkers, as there is no way to express parametrization overloads. Having it used for a new typing feature would be confusing for users (and would require changes in code linters)."
  - concern types: Readability / teachability
- **Rejected Ideas (PEP 821)** (PEP 821 § Rejected Ideas, 2026), score 0.286
  - context: "- Combining Unpack[TD] with Concatenate. With such support, one could write Callable[Concatenate[int, Unpack[TD], P], R] which in turn would allow a keyword-only parameter between *args and kwargs, i.e. def func(*args: Any, a: int, kwargs: Any) -> R: ... which is currently not allowed per 612."

## Objections to prepare for

- **Backward compatibility**, weight 0.302
  - "To retain backwards compatibility, type checkers should not infer a TypedDict type unless it is sufficiently clear that this is desired by the programmer." (PEP 589 (compat))
  - "Because extra_items is an opt-in feature, no existing codebase will break due to this change." (PEP 728 (compat))
- **Readability / teachability**, weight 0.178
  - "This would add more confusion for users because it would mean that in some contexts the meaning of Optional[] is different than in other contexts, and it would be easy to overlook the flag." (PEP 655 (rejected idea: Change Optional to mean “optional item” in certain contexts instead of “nullable”))
  - "Having it used for a new typing feature would be confusing for users (and would require changes in code linters)." (PEP 764 (rejected idea: Using dict or typing.Dict with a single type argument))
- **Runtime behavior / introspection**, weight 0.165
  - "TypedDict objects are regular dictionaries at runtime, and TypedDict cannot be used with other dictionary-like or mapping-like classes, including subclasses of dict." (PEP 589 (rejected idea: Rejected Alternatives (PEP 589)))
  - "Tools that specifically rely on introspecting annotations at runtime (tools that parse Python files are obviously unaffected) that want to extract the annotations unevaluated and process them in some way are possibly in more trouble." (PEP 827 (compat))
- **Insufficient motivation / scope**, weight 0.095
  - "- The types don't appear in an annotation context, so their evaluation will not be deferred." (PEP 728 (rejected idea: Support a New Syntax of Specifying Keys))
- **Cost of new syntax**, weight 0.095
  - "By introducing a new syntax that allows specifying string keys, we could deprecate the functional syntax of defining TypedDict types and address the key conflict issues if we decide to reserve a special key to type extra items." (PEP 728 (rejected idea: Support a New Syntax of Specifying Keys))
- **Impact on libraries and tools**, weight 0.089
  - "Such functionality can be provided by a third-party library using the typing_inspect [#typing_inspect]_ third-party module, for example." (PEP 589 (rejected idea: Rejected Alternatives (PEP 589)))

## Read first (in this order)

1. PEP 484: Type Hints (foundation of PEP 589)
2. PEP 483: The Theory of Type Hints (foundation of PEP 589)
3. PEP 586: Literal Types (foundation of PEP 589)
4. PEP 591: Adding a final qualifier to typing (foundation of PEP 589)
5. PEP 589: TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys (closest prior proposal)
6. PEP 692: Using TypedDict for more precise **kwargs typing (foundation of PEP 728)
7. PEP 728: TypedDict with Typed Extra Items (closest prior proposal)
8. PEP 764: Inline typed dictionaries (closest prior proposal)

## People to engage

- Victorien Plot (author of PEP 764; last active 2024)
- Jelle Zijlstra (sponsor of PEP 692, PEP 728, PEP 821; last active 2026)
- Eric Traut (sponsor of PEP 764; last active 2024)
- Daniel Sperber (author of PEP 821; last active 2026)
- Zixuan James Li (author of PEP 728; last active 2023)

## Where to discuss

discuss.python.org (Discourse): most recent related PEP (PEP 821, 2026) was discussed there.

## Track record of this area

Concepts: Inline TypedDict, TypedDict. Of the 8 PEPs focused on them: 5 accepted, 0 rejected/withdrawn, 3 open.

PEP 589 (Final), PEP 655 (Final), PEP 692 (Final), PEP 705 (Final), PEP 728 (Final), PEP 764 (Draft), PEP 821 (Draft), PEP 827 (Draft)

