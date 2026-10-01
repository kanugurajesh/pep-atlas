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

- **Shorthand with Slices** (PEP 727 § Rejected Ideas / Shorthand with Slices, 2023), score 0.397
  - context: "In the discussion, it was suggested to use a shorthand with slices:"
  - concern types: Runtime behavior / introspection
- **Change Optional to mean “optional item” in certain contexts instead of “nullable”** (PEP 655 § Rejected Ideas / Change Optional to mean “optional item” in certain contexts instead of “nullable”, 2021), score 0.359
  - stated reason: "This would add more confusion for users because it would mean that in some contexts the meaning of Optional[] is different than in other contexts, and it would be easy to overlook the flag."
  - concern types: Readability / teachability
  - ↻ later revisited by **PEP 705** (TypedDict: Read-only items, Final)
- **Why not use tool X?** (PEP 675 § Rejected Alternatives / Why not use tool X?, 2021), score 0.302
  - stated reason: "The problem is that many perfectly safe SQL queries are dynamically built out of string literals, as shown in the `Motivation`_ section. To use these tools would require significantly restricting developers' ability to build SQL queries."
  - concern types: Readability / teachability
- **Provide a special intersection type construct** (PEP 544 § Rejected/Postponed Ideas / Provide a special intersection type construct, 2017), score 0.284
  - stated reason: "However, it is not yet clear how popular/useful it will be and implementing this in type checkers for non-protocol classes could be difficult."
- **Extended Syntax Supporting Named and Optional Arguments** (PEP 677 § Rejected Alternatives / Extended Syntax Supporting Named and Optional Arguments, 2021), score 0.264
  - stated reason: "We decided against proposing it for the following reasons: - The implementation would have been more difficult, and usage stats demonstrate that fewer than 3% of use cases would benefit from any of the added features. - The group that debated these proposals was split down the middle about whether these changes are…"
  - concern types: Readability / teachability, Cost of new syntax

## Objections to prepare for

- **Readability / teachability**, weight 0.42 (typical for: new syntax)
  - "This would add more confusion for users because it would mean that in some contexts the meaning of Optional[] is different than in other contexts, and it would be easy to overlook the flag." (PEP 655 (rejected idea: Change Optional to mean “optional item” in certain contexts instead of “nullable”))
  - "These tools are powerful but involve considerable overhead in setting up the tool in CI, defining "taint" sinks and sources, and teaching developers how to use them." (PEP 675 (rejected idea: Why not use tool X?))
- **Cost of new syntax**, weight 0.221 (typical for: new syntax)
  - "We confirmed that the current proposal is forward-compatible with extended syntax by implementing a grammar and AST for this extended syntax on top of our reference implementation of this PEP's grammar." (PEP 677 (rejected idea: Extended Syntax Supporting Named and Optional Arguments))
  - "The notation T|None introduced by 604 to write Optional[T] is a fine alternative to T? and does not require new syntax." (PEP 645 (decision))
- **Backward compatibility**, weight 0.142 (typical for: new syntax)
  - "We do want stub files, but they are primarily useful for adding type hints to existing code that doesn't lend itself to adding type hints, e.g. 3rd party packages, code that needs to support both Python 2 and Python 3, and especially…" (PEP 484 (compat))
  - "? is currently unused in Python syntax, therefore this PEP is fully backwards compatible." (PEP 645 (compat))
- **Ambiguity / inconsistency**, weight 0.131
  - "Using T? to mean T|None is also inconsistent with TypeScript where it roughly means NotRequired[T]." (PEP 645 (decision))
- **Runtime behavior / introspection**, weight 0.087
  - "At runtime, ~typing.Annotated requires at least two arguments, and it requires the first argument to be type, it crashes if it is a slice." (PEP 727 (rejected idea: Shorthand with Slices))

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

