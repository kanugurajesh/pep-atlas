# Proposal assessment

> Python should enforce type hints at runtime: when a function is called with arguments of the wrong type it should raise TypeError, so annotations are actually guaranteed.

## Verdict: Builds on an existing area (no direct precedent)  (confidence: medium)

No PEP matches closely enough to call it the same proposal, but it builds on established concepts (Runtime annotation access, Runtime type enforcement). Nearest prior work: PEP 526 (Syntax for Variable Annotations). Expect to be measured against the decisions made there.

> ⚠ May conflict with a stated non-goal of PEP 484: "It should also be emphasized that Python will remain a dynamically typed language, and the authors have no desire to ever make type hints mandatory, even by convention."

## How the input was read

| Concept | Matched on | Specificity |
|---|---|---|
| Runtime annotation access | at runtime | 0.26 |
| Runtime type enforcement | enforce type | 0.41 |

Kind of change: runtime change

## Closest prior PEPs

- **PEP 526: Syntax for Variable Annotations** (Final, 2016), score 0.38
  - why: introduces Runtime annotation access; mentions Runtime type enforcement; shared wording: annotation, hint, function, runtime
- **PEP 563: Postponed Evaluation of Annotations** (Superseded, 2017) → superseded by PEP 649, PEP 749, score 0.331
  - why: extends Runtime annotation access; mentions Runtime type enforcement; shared wording: annotation, hint, runtime, function
- **PEP 593: Flexible function and variable annotations** (Final, 2019), score 0.316
  - why: extends Runtime annotation access; shared wording: annotation, function, runtime
- **PEP 849: More Expressive Type Expressions** (Draft, 2026), score 0.31
  - why: proposes Runtime annotation access; shared wording: annotation, function, runtime
- **PEP 649: Deferred Evaluation Of Annotations Using Descriptors** (Final, 2021), score 0.294
  - why: extends Runtime annotation access; shared wording: annotation, function, hint, runtime

## Similar ideas that were turned down

- **The problem of forward declarations** (PEP 484 § Rejected Alternatives / The problem of forward declarations, 2014), score 0.427
  - stated reason: "Apart from circular imports this is rarely a problem: "use" here means "look up at runtime", and with most "forward" references there is no problem in ensuring that a name is defined before the function using it is called. The problem with type hints is that annotations (per 3107, and similar to default values) are…"
  - concern types: Backward compatibility, Insufficient motivation / scope, Runtime behavior / introspection
  - ↻ later revisited by **PEP 649** (Deferred Evaluation Of Annotations Using Descriptors, Final)
- **The double colon** (PEP 484 § Rejected Alternatives / The double colon, 2014), score 0.421
  - stated reason: "A few creative souls have tried to invent solutions for this problem. There are several things wrong with this idea, however."
  - concern types: Ambiguity / inconsistency, Runtime behavior / introspection, Cost of new syntax
- **Runtime Checkable LiteralString** (PEP 675 § Rejected Alternatives / Runtime Checkable ``LiteralString``, 2021), score 0.419
  - stated reason: "Such runtime errors would be a more robust defense mechanism than type errors, which can potentially be suppressed, ignored, or never even seen if the author does not use a type checker."
  - concern types: Insufficient motivation / scope
- **Runtime enforcement** (PEP 698 § Rejected Alternatives / Runtime enforcement, 2022), score 0.393
  - stated reason: "We rejected this for four reasons: - For users of static type checking, it is not clear this brings any benefits. - There would be at least some performance overhead, leading to projects importing slower with runtime enforcement. We estimate the @overrides.overrides implementation takes around 100 microseconds, which…"
  - concern types: Ambiguity / inconsistency, Runtime cost, Runtime behavior / introspection
- **Stated non-goals of PEP 484** (PEP 484 § Rationale and Goals / Non-goals, 2014), score 0.372
  - stated reason: "It should also be emphasized that Python will remain a dynamically typed language, and the authors have no desire to ever make type hints mandatory, even by convention."
  - concern types: Impact on libraries and tools, Runtime cost, Runtime behavior / introspection

## Objections to prepare for

- **Runtime behavior / introspection**, weight 0.306 (typical for: runtime change)
  - "Apart from circular imports this is rarely a problem: "use" here means "look up at runtime", and with most "forward" references there is no problem in ensuring that a name is defined before the function using it is called." (PEP 484 (rejected idea: The problem of forward declarations))
  - "* It's actually a feature that type hints are evaluated at runtime." (PEP 484 (rejected idea: The double colon))
- **Backward compatibility**, weight 0.162 (typical for: runtime change)
  - "This of course would run afoul of backwards compatibility, since the Python interpreter doesn't actually know whether a particular annotation is meant to be a type hint or something else." (PEP 484 (rejected idea: The problem of forward declarations))
  - "This PEP is fully backwards compatible." (PEP 526 (compat))
- **Ambiguity / inconsistency**, weight 0.13
  - "For example, it was proposed to use a double colon () for type hints, solving two problems at once: disambiguating between type hints and other annotations, and changing the semantics to preclude runtime evaluation." (PEP 484 (rejected idea: The double colon))
  - "We estimate the @overrides.overrides implementation takes around 100 microseconds, which is fast but could still add up to a second or more of extra initialization time in million-plus line codebases, which is exactly where we think…" (PEP 698 (rejected idea: Runtime enforcement))
- **Runtime cost**, weight 0.111 (typical for: runtime change)
  - "- For users of static type checking, it is not clear this brings any benefits. - There would be at least some performance overhead, leading to projects importing slower with runtime enforcement." (PEP 698 (rejected idea: Runtime enforcement))
  - "Using type hints for performance optimizations is left as an exercise for the reader." (PEP 484 (rejected idea: Stated non-goals of PEP 484))
- **Impact on libraries and tools**, weight 0.106
  - "While the proposed typing module will contain some building blocks for runtime type checking -- in particular the get_type_hints() function -- third party packages would have to be developed to implement specific runtime type checking…" (PEP 484 (rejected idea: Stated non-goals of PEP 484))
  - "However, there is another set of compatibility problems: new code that is written assuming 649 semantics, but uses existing tools that eagerly evaluate annotations." (PEP 749 (compat))
- **Insufficient motivation / scope**, weight 0.103
  - "Such a __future__ import statement may be proposed in a separate PEP." (PEP 484 (rejected idea: The problem of forward declarations))
  - "While runtime taint checking on strings, similar to Perl's taint, has been considered and attempted in the past, and others may consider it in the future, such extensions are out of scope for this PEP." (PEP 675 (rejected idea: Runtime Checkable LiteralString))

## Read first (in this order)

1. PEP 3107: Function Annotations (foundation of PEP 563)
2. PEP 484: Type Hints (foundation of PEP 526)
3. PEP 483: The Theory of Type Hints (foundation of PEP 544 → PEP 563)
4. PEP 526: Syntax for Variable Annotations (closest prior proposal)
5. PEP 544: Protocols: Structural subtyping (static duck typing) (foundation of PEP 563)
6. PEP 560: Core support for typing module and generic types (foundation of PEP 563)
7. PEP 563: Postponed Evaluation of Annotations (closest prior proposal)
8. PEP 593: Flexible function and variable annotations (closest prior proposal)

## People to engage

- Imogen Hergeth (author of PEP 849; last active 2026)
- Łukasz Langa (author of PEP 563, PEP 585; last active 2019)
- Ivan Levkivskyi (author of PEP 526; sponsor of PEP 593; last active 2019)
- Jelle Zijlstra (sponsor of PEP 849; last active 2026)
- Larry Hastings (author of PEP 649; last active 2021)

## Where to discuss

discuss.python.org (Discourse): most recent related PEP (PEP 849, 2026) was discussed there.

## Track record of this area

Concepts: Runtime annotation access, Runtime type enforcement. Of the 7 PEPs focused on them: 6 accepted, 0 rejected/withdrawn, 1 open.

PEP 526 (Final), PEP 563 (Superseded), PEP 585 (Final), PEP 593 (Final), PEP 649 (Final), PEP 749 (Final), PEP 849 (Draft)

