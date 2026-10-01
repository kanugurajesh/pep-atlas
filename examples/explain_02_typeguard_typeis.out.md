# How this came to be

> Why are there two narrowing helpers, TypeGuard and TypeIs, and why doesn't TypeGuard narrow in the negative case?

Concepts: TypeIs, TypeGuard, Type narrowing

## Timeline

- **2020: PEP 647**, User-Defined Type Guards [Final, introduces TypeGuard, Type narrowing]
- **2023: PEP 724**, Stricter Type Guards [Withdrawn, proposes TypeGuard, Type narrowing] → superseded by PEP 742
  - why it stopped: "This PEP is withdrawn. The Typing Council was unable to reach consensus on this proposal, and the authors decided to withdraw it."
- **2024: PEP 742**, Narrowing types with TypeIs [Final, introduces TypeIs, TypeGuard, Type narrowing]

## Alternatives that were turned down along the way

- **TypeGuard with a second output type** (PEP 724, 2023)
  - "It was rejected because it was considered too complicated and addressed only one of the two main limitations of TypeGuard."
  - ↻ revisited by PEP 742
- **Alternative names** (PEP 742, 2024)
  - "This PEP currently proposes the name TypeIs, emphasizing that the special form TypeIs[T] returns whether the argument is of type T, and mirroring TypeScript's syntax. Other names were considered, including in an earlier version of this PEP."
- **Change the behavior of TypeGuard** (PEP 742, 2024)
  - "This proposal has some important advantages: because it does not require any runtime changes, it requires changes only in type checkers, making it easier for users to take advantage of the new, usually more intuitive behavior. However, this approach has some major problems."
- **Do nothing** (PEP 742, 2024)
  - "As for this PEP, it introduces two special forms with very similar semantics, and it potentially creates a long migration path for users currently using TypeGuard who would be better off with different narrowing semantics. However, we believe that the limitations of the current TypeGuard, as outlined in the…"
- **Narrowing of Arbitrary Parameters** (PEP 647, 2020)
  - "For this reason, it was decided unnecessary to burden the Python implementation of user-defined type guards with additional complexity to support a contrived use case."
  - ↻ revisited by PEP 742
- **Enforcing Strict Narrowing** (PEP 647, 2020)
  - "For instance, the is_str_list example above would be considered invalid because List[str] is not a subtype of List[object] because of invariance rules. This was rejected because it was deemed cumbersome and unnecessary."
  - ↻ revisited by PEP 742

