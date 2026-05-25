# Test Design Guide

## Purpose

Translate confirmed PRD analysis output into a complete, prioritized set of test cases
with full traceability back to requirements.

## Methodology

### 1. Scope Confirmation

Before generating cases, verify:

- The module list matches what was confirmed in PRD analysis.
- No new modules have been added without user consent.
- Any user supplements from the iteration phase are incorporated.

### 2. Scenario Derivation

For each module and test point, derive scenarios using these techniques:

**Equivalence partitioning** -- group inputs into classes that should produce the same behavior.

**Boundary value analysis** -- test at exact limits (min, max, min-1, max+1).

**State transition** -- identify states and test each valid/invalid transition.

**Error guessing** -- based on common failure patterns (null, empty, duplicate, timeout).

### 3. Case Structuring

Each case follows the template in `../assets/case-template.md`:

- Module, scenario type, priority, preconditions, steps, expected result.
- One assertion per case (atomic, independently verifiable).

### 4. Priority Assignment

Apply priority rules from `SKILL.md`:

- P0: release-blocking, core flow.
- P1: significant but has workaround.
- P2: minor, cosmetic, low-frequency.

When uncertain, default to P1 and flag for user review.

### 5. Traceability

Each case must reference the requirement bullet or test point it validates.
Format: `[REQ-{module}-{number}]` or the original test point text.

### 6. Coverage Review

After generation, produce a coverage matrix:

| Requirement | Happy | Exception | Boundary | Permission |
|-------------|-------|-----------|----------|------------|
| REQ-001     | TC-01 | TC-05     | TC-08    | --         |

Flag any requirement with zero coverage as a potential gap.

## Diff Mode

When iterating on existing cases:

- Show only added/modified/removed cases.
- Use `+` / `-` / `~` markers.
- Preserve case IDs for unchanged cases.
- Re-emit the coverage matrix delta.
