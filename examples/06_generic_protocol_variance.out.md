# Proposal assessment

> Type checkers should infer the variance of type parameters on Protocol classes automatically instead of requiring covariant=True / contravariant=True on the TypeVar.

## Verdict: Previously rejected as an alternative  (confidence: medium)

Something close to this was considered and rejected as an alternative in PEP 544 ("Overriding inferred variance of protocol classes").

## How the input was read

| Concept | Matched on | Specificity |
|---|---|---|
| Protocols (structural subtyping) | Protocol, Protocol classes | 0.39 |
| TypeVar | TypeVar | 0.29 |
| Variance | contravariant, covariant, variance | 0.37 |

Kind of change: checker semantics

## Closest prior PEPs

- **PEP 695: Type Parameter Syntax** (Final, 2022), score 0.468
  - why: extends TypeVar; extends Variance; mentions Protocols (structural subtyping); shared wording: variance, typevar, parameter, class
- **PEP 544: Protocols: Structural subtyping (static duck typing)** (Final, 2017), score 0.396
  - why: introduces Protocols (structural subtyping); mentions TypeVar; mentions Variance; shared wording: protocol, covariant, variance, class, checker
- **PEP 484: Type Hints** (Final, 2014), score 0.372
  - why: introduces TypeVar; introduces Variance; shared wording: class, parameter
- **PEP 673: Self Type** (Final, 2021), score 0.328
  - why: extends TypeVar; shared wording: infer, typevar, protocol, class, checker
- **PEP 696: Type Defaults for Type Parameters** (Final, 2022), score 0.194
  - why: extends TypeVar; shared wording: parameter, typevar

## Similar ideas that were turned down

- **Overriding inferred variance of protocol classes** (PEP 544 § Rejected/Postponed Ideas / Overriding inferred variance of protocol classes, 2017), score 0.875
  - stated reason: "However, it was decided not to do this because of several downsides: * Declared protocol invariance breaks transitivity of sub-typing."
- **Explicit Variance** (PEP 695 § Rejected Ideas / Explicit Variance, 2022), score 0.709
  - stated reason: "We rejected this idea because variance can generally be inferred, and most modern programming languages do infer variance based on usage. Variance is an advanced topic that many developers find confusing, so we want to eliminate the need to understand this concept for most Python developers."
  - concern types: Readability / teachability
- **Construction of TypeVarTuple** (PEP 646 § Rationale and Rejected Ideas / Construction of ``TypeVarTuple``, 2020), score 0.443
  - stated reason: "Once we'd decided that a variadic type variable should behave like a Tuple, we also considered TypeVar(bound=Tuple), which is similarly intuitive and accomplishes most what we wanted without requiring any new arguments to TypeVar. However, we realised this may constrain us in the future, if for example we want type…"
  - concern types: Readability / teachability
  - ↻ later revisited by **PEP 696** (Type Defaults for Type Parameters, Final)

## Objections to prepare for

- **Readability / teachability**, weight 0.539
  - "Variance is an advanced topic that many developers find confusing, so we want to eliminate the need to understand this concept for most Python developers." (PEP 695 (rejected idea: Explicit Variance))
  - "Once we'd decided that a variadic type variable should behave like a Tuple, we also considered TypeVar(bound=Tuple), which is similarly intuitive and accomplishes most what we wanted without requiring any new arguments to TypeVar." (PEP 646 (rejected idea: Construction of TypeVarTuple))
- **Backward compatibility**, weight 0.192
  - "We do want stub files, but they are primarily useful for adding type hints to existing code that doesn't lend itself to adding type hints, e.g. 3rd party packages, code that needs to support both Python 2 and Python 3, and especially…" (PEP 484 (compat))
  - "This PEP is fully backwards compatible." (PEP 544 (compat))
- **Cost of new syntax**, weight 0.096
  - "Note that the use of the star operator in this context requires a grammar change, and is therefore available only in new versions of Python." (PEP 646 (compat))
- **Type safety / soundness**, weight 0.058 (typical for: checker semantics)
- **Burden on type checkers**, weight 0.058 (typical for: checker semantics)
- **Ambiguity / inconsistency**, weight 0.058 (typical for: checker semantics)

## Read first (in this order)

1. PEP 484: Type Hints (closest prior proposal)
2. PEP 483: The Theory of Type Hints (foundation of PEP 695)
3. PEP 544: Protocols: Structural subtyping (static duck typing) (closest prior proposal)
4. PEP 563: Postponed Evaluation of Annotations (foundation of PEP 695)
5. PEP 612: Parameter Specification Variables (foundation of PEP 695)
6. PEP 613: Explicit Type Aliases (foundation of PEP 695)
7. PEP 646: Variadic Generics (foundation of PEP 695)
8. PEP 695: Type Parameter Syntax (closest prior proposal)

## People to engage

- Guido van Rossum (sponsor of PEP 695; decision delegate for PEP 544; author of PEP 484; last active 2022)
- Eric Traut (author of PEP 695, PEP 724; last active 2023)
- James Hilton-Balfe (author of PEP 673, PEP 696; last active 2022)
- Jelle Zijlstra (sponsor of PEP 673, PEP 696, PEP 724; last active 2023)
- Jukka Lehtosalo (author of PEP 484, PEP 544; last active 2017)

## Where to discuss

discuss.python.org (Discourse): most recent related PEP (PEP 724, 2023) was discussed there.

## Track record of this area

Concepts: Protocols (structural subtyping), TypeVar, Variance. Of the 6 PEPs focused on them: 6 accepted, 0 rejected/withdrawn, 0 open.

PEP 484 (Final), PEP 544 (Final), PEP 646 (Final), PEP 673 (Final), PEP 695 (Final), PEP 696 (Final)

