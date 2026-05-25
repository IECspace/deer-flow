# Regression: Double Approval Bug

## Incident Summary

Two QA leads approved the same replay task within seconds of each other.
The task was executed twice, causing duplicate test results and data confusion.

## Root Cause

No optimistic lock on task status. Both approval requests read `pending` state
and both succeeded the UPDATE.

## Test Case That Would Catch This

| Case Name | Priority | Precondition | Steps | Expected Result |
|-----------|----------|--------------|-------|-----------------|
| Concurrent approval of same task | P0 | Task in pending state; two sessions active | 1. Session A clicks Approve\n2. Session B clicks Approve within 1s | Only one succeeds; the other gets "Task already approved" error |

## Prevention Rule

For any feature involving state transitions:
- Always include a concurrency test case.
- Verify the DB uses optimistic locking or SELECT FOR UPDATE.
- Check that the API returns a clear error (not silent success) on conflict.

## How This Helps

When generating test cases for stateful operations:
- Always add a "concurrent modification" P0 case.
- Reference this incident as justification for the test.
