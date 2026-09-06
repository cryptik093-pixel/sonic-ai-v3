# CREATE -> BUILD -> VALIDATE -> LOCK Protocol

## Purpose
Preserve intention through implementation.

```text
CREATE
Why should this exist?
What problem does it solve?
What is the intended behavior?

DESIGN
What contract represents that intention?

BUILD
Implement only the approved contract.

VALIDATE
Did observed reality match the intention and contract?

LOCK
Tests
documentation
decision record
commit/checkpoint
baseline
```

## Canonical shorthand

`INTENT -> CONTRACT -> BUILD -> EVIDENCE -> VALIDATION -> LOCK`

## Rule
A technically successful build is not LOCKED until evidence demonstrates that the implementation satisfies the original intention.
