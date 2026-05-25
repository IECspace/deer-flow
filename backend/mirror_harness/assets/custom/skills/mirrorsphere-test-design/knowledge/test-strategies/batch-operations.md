# Batch Operations Test Strategy

## Context

Mirrorsphere has multiple batch operations (batch approve, batch import, batch move).
This strategy applies to any batch feature.

## Required Test Scenarios

### Size Boundaries
- Empty batch (0 items) → expect rejection or disabled action.
- Single item batch (1 item) → should work like single operation.
- Exactly at limit (e.g., 50) → should succeed.
- One over limit (e.g., 51) → should be rejected with clear message.

### Atomicity
- All items valid → full success.
- One item invalid → entire batch fails (if atomic) or partial success (if best-effort).
- Verify: which model is used? PRD must specify.

### Concurrency
- Same item in two concurrent batches → only one should succeed.
- Item state changes between selection and submission → should fail validation.

### Performance
- Maximum batch size under normal load → latency acceptable?
- Multiple users submitting large batches simultaneously → no timeout?

## How This Helps

When generating test cases for any batch operation feature:
- Always include the 4 categories above as a baseline.
- Adjust specific values (limits, error messages) per feature.
- Flag if the PRD doesn't specify atomicity behavior.
