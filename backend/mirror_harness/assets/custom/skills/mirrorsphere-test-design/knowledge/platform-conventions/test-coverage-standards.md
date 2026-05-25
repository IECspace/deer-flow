# Test Coverage Standards

## Context

Platform-wide conventions for test case coverage and prioritization.

## Coverage Requirements by Priority

| Priority | Coverage Expectation |
|----------|---------------------|
| P0 | Must be tested in all environments (test, pre, prod) before release |
| P1 | Must pass in test and pre environments |
| P2 | Must pass in test environment; pre is recommended |
| P3 | Test environment coverage sufficient |

## Minimum Case Distribution

For a typical feature:
- P0: 20-30% of total cases (core flows, permission gates, data integrity).
- P1: 30-40% of total cases (important variations, key error paths).
- P2: 20-30% of total cases (secondary scenarios, less common paths).
- P3: 10-20% of total cases (edge cases, cosmetic checks).

If a generated set is heavily skewed (e.g., 80% P0), re-evaluate whether
priorities are correctly assigned.

## Naming Conventions

- Case names: action-oriented, start with verb or describe the scenario.
- Avoid: "Test case 1", "Check if works", "Verify functionality".
- Prefer: "Batch approve 50 tasks at limit", "Reject expired pending task".

## Async Operation Testing

For operations involving async side effects (notifications, queue processing):
- Separate the trigger test (API returns success) from the effect test (notification received).
- Specify acceptable delay: "Notification arrives within 5 seconds".
- Include a failure mode case: "Notification fails but main operation succeeds".

## How This Helps

When generating test cases:
- Use priority distribution as a self-check before presenting to user.
- Apply naming conventions to all generated case names.
- For async features, always split into trigger + effect cases.
