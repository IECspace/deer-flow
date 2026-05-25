# Test Case Template

## Table Columns

| Column | Required | Description |
|--------|----------|-------------|
| Case Name | Yes | Descriptive, action-oriented name. Maps to API `feature` field. |
| Priority | Yes | P0 / P1 / P2 / P3. Maps to API `level` (1/2/3/4). |
| Precondition | No | State required before execution. Maps to API `precondition`. |
| Steps | Yes | Numbered action sequence. Use `\n` between steps. Maps to API `steps`. |
| Expected Result | Yes | Observable, verifiable outcome. Maps to API `expected_result`. |
| Actual Result | No | Always empty at generation time. Filled during test execution. |
| Remark | No | Additional notes, edge case context, or references. Maps to API `remark`. |

## Priority Rules

| Priority | When to use | API level value |
|----------|-------------|-----------------|
| P0 | Core user flow; release-blocking | 1 |
| P1 | Important functionality; workaround exists | 2 |
| P2 | Secondary scenario; low frequency | 3 |
| P3 | Edge case; cosmetic or rarely triggered | 4 |

## Writing Rules

- Case Name: start with a verb or describe the scenario concisely.
- Steps: must be reproducible without implicit knowledge.
- Expected Result: must be objectively verifiable (avoid "works correctly").
- One assertion per case. If multiple outcomes, split into separate cases.
- Precondition: achievable from a clean state; state roles, data, and environment.
