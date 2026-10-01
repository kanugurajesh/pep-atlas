# How this came to be

> Why does from __future__ import annotations exist, and why was it never made the default?

Concepts: Postponed evaluation (stringified annotations), Deferred evaluation (lazy annotations)

## Timeline

- **2017: PEP 563**, Postponed Evaluation of Annotations [Superseded, introduces Postponed evaluation (stringified annotations)] → superseded by PEP 649, PEP 749
- **2021: PEP 649**, Deferred Evaluation Of Annotations Using Descriptors [Final, introduces Deferred evaluation (lazy annotations)]
- **2024: PEP 749**, Implementing PEP 649 [Final, extends Deferred evaluation (lazy annotations)]
- **2026: PEP 849**, More Expressive Type Expressions [Draft, proposes Deferred evaluation (lazy annotations)]

## Alternatives that were turned down along the way

- **New annotationlib module: rejected alternatives** (PEP 749, 2024)
  - "- annotations: The most obvious name, but it may cause confusion with the existing from __future__ import annotations, because users may have both import annotations and from __future__ import annotations in the same module. There is a PyPI package :pypi:`annotations`, but it had only a single release in 2015 and…"
- **The future of from __future__ import annotations: rejected alternatives** (PEP 749, 2024)
  - "However, this would break code that works in 3.13 under the following set of conditions: * __future__ import annotations is active * There are annotations that rely on forward references * Annotations are eagerly evaluated at import time, for example by a metaclass or class or function decorator. However, this is…"
- **Introducing a new dictionary for the string literal form instead** (PEP 563, 2017)
  - "While postponed evaluation fixes the forward reference problem, it also makes it impossible to access function-level locals anymore."
- **Annotations and metaclasses: rejected alternatives** (PEP 749, 2024)
  - "Instead, users should call function in annotationlib that invoke the type descriptors directly. (Implemented in gh-122074.) * Ensure that the entry is never present in the class dictionary, or at least never added by logic in the language core."
- **Structural Evaluation Format (Format.TYPE)** (PEP 835, 2026)
  - "This was rejected."

