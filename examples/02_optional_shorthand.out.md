# Proposal assessment

> Allow T? as a shorthand for Optional[T] in annotations, like Kotlin and TypeScript do.

## Verdict: Previously rejected  (confidence: high)

PEP 645 (Allow writing optional types as x?) proposed this and was withdrawn. A new attempt has to answer the reasons recorded in its decision.

## How the input was read

| Concept | Matched on | Specificity |
|---|---|---|
| `X?` optional shorthand | T? | 0.55 |
| Union types | Optional | 0.32 |

Kind of change: new syntax

## Closest prior PEPs

- **PEP 645: Allow writing optional types as x?** (Withdrawn, 2020), score 0.84
  - why: proposes Union types; proposes `X?` optional shorthand; shared wording: optional, allow
  - decision: "The notation T|None introduced by 604 to write Optional[T] is a fine alternative to T? and does not require new syntax. Using T? to mean T|None is also inconsistent with TypeScript where it roughly means NotRequired[T]. Such inconsistency would likely confuse folks coming from TypeScript to…"
- **PEP 484: Type Hints** (Final, 2014), score 0.233
  - why: introduces Union types; shared wording: annotation
- **PEP 604: Allow writing union types as X | Y** (Final, 2019), score 0.224
  - why: extends Union types; shared wording: allow
- **PEP 727: Documentation in Annotated Metadata** (Withdrawn, 2023), score 0.181
  - why: shared wording: shorthand, typescript, like
  - decision: "The reception of this PEP was mostly negative, with concerns raised about verbosity and readability. As a result, this PEP has been withdrawn."
- **PEP 835: Shorthand syntax for Annotated type metadata** (Draft, 2026), score 0.162
  - why: mentions Union types; shared wording: shorthand, allow

## Similar ideas that were turned down

- **Change Optional to mean “optional item” in certain contexts instead of “nullable”** (PEP 655 § Rejected Ideas / Change Optional to mean “optional item” in certain contexts instead of “nullable”, 2021), score 0.359
  - stated reason: "This would add more confusion for users because it would mean that in some contexts the meaning of Optional[] is different than in other contexts, and it would be easy to overlook the flag."
  - concern types: Readability / teachability
  - ↻ later revisited by **PEP 705** (TypedDict: Read-only items, Final)
- **Special syntax around the key of a TypedDict item** (PEP 655 § Rejected Ideas / Special syntax around the *key* of a TypedDict item, 2021), score 0.251
  - stated reason: "This notation would require Python grammar changes and it is not believed that marking TypedDict items as required or potentially-missing would meet the high bar required to make such grammar changes. This notation causes Optional[] to take on different meanings depending on where it is positioned, which is…"
  - concern types: Ambiguity / inconsistency, Readability / teachability, Cost of new syntax
  - ↻ later revisited by **PEP 705** (TypedDict: Read-only items, Final)
- **Misalignment with how unions are subdivided** (PEP 655 § Rejected Ideas / Marking absence of a value with a special constant / Misalignment with how unions are subdivided, 2021), score 0.212
  - stated reason: "However if we were to allow Union[..., Missing] you’d either have to eliminate the Missing case with hasattr for object attributes: or a check against locals() for local variables:"
  - concern types: Ambiguity / inconsistency, Runtime behavior / introspection

## Objections to prepare for

- **Readability / teachability**, weight 0.355 (typical for: new syntax)
  - "This would add more confusion for users because it would mean that in some contexts the meaning of Optional[] is different than in other contexts, and it would be easy to overlook the flag." (PEP 655 (rejected idea: Change Optional to mean “optional item” in certain contexts instead of “nullable”))
  - "This notation causes Optional[] to take on different meanings depending on where it is positioned, which is inconsistent and confusing." (PEP 655 (rejected idea: Special syntax around the key of a TypedDict item))
- **Ambiguity / inconsistency**, weight 0.234
  - "This notation causes Optional[] to take on different meanings depending on where it is positioned, which is inconsistent and confusing." (PEP 655 (rejected idea: Special syntax around the key of a TypedDict item))
  - "Weird and inconsistent." (PEP 655 (rejected idea: Misalignment with how unions are subdivided))
- **Cost of new syntax**, weight 0.221 (typical for: new syntax)
  - "This notation would require Python grammar changes and it is not believed that marking TypedDict items as required or potentially-missing would meet the high bar required to make such grammar changes." (PEP 655 (rejected idea: Special syntax around the key of a TypedDict item))
  - "The notation T|None introduced by 604 to write Optional[T] is a fine alternative to T? and does not require new syntax." (PEP 645 (decision))
- **Backward compatibility**, weight 0.143 (typical for: new syntax)
  - "We do want stub files, but they are primarily useful for adding type hints to existing code that doesn't lend itself to adding type hints, e.g. 3rd party packages, code that needs to support both Python 2 and Python 3, and especially…" (PEP 484 (compat))
  - "? is currently unused in Python syntax, therefore this PEP is fully backwards compatible." (PEP 645 (compat))
- **Runtime behavior / introspection**, weight 0.047
  - "Furthermore the use of Union[..., Missing] doesn’t align with the usual ways that union values are broken down: Normally you can eliminate components of a union type using isinstance checks:" (PEP 655 (rejected idea: Misalignment with how unions are subdivided))

## Read first (in this order)

1. PEP 3107: Function Annotations (foundation of PEP 563 → PEP 604)
2. PEP 484: Type Hints (closest prior proposal)
3. PEP 526: Syntax for Variable Annotations (foundation of PEP 604)
4. PEP 544: Protocols: Structural subtyping (static duck typing) (foundation of PEP 563 → PEP 604)
5. PEP 563: Postponed Evaluation of Annotations (foundation of PEP 604)
6. PEP 585: Type Hinting Generics In Standard Collections (foundation of PEP 604)
7. PEP 604: Allow writing union types as X | Y (closest prior proposal)
8. PEP 645: Allow writing optional types as x? (closest prior proposal (read why it failed))

## People to engage

- Maggie Moss (author of PEP 604, PEP 645; last active 2020)
- Guido van Rossum (sponsor of PEP 645; author of PEP 484; decision delegate for PEP 604; last active 2020)
- Till Varoquaux (author of PEP 835; last active 2026)
- Daniel W. Park (author of PEP 827; last active 2026)
- Michael J. Sullivan (author of PEP 827; last active 2026)

## Where to discuss

discuss.python.org (Discourse): most recent related PEP (PEP 835, 2026) was discussed there.

## Track record of this area

Concepts: `X?` optional shorthand, Union types. Of the 3 PEPs focused on them: 2 accepted, 1 rejected/withdrawn, 0 open.

PEP 484 (Final), PEP 604 (Final), PEP 645 (Withdrawn)

