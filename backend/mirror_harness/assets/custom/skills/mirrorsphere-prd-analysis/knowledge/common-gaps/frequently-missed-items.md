# Frequently Missed Items in PRDs

## Context

Based on past PRD reviews, these items are commonly omitted or underspecified.

## Checklist of Common Gaps

### 1. Concurrency & Race Conditions
- What happens if two users act on the same resource simultaneously?
- Is the operation idempotent? What prevents duplicate submissions?

### 2. Pagination & Limits
- Large list views: is pagination specified? Default page size?
- Bulk operations: is there a max batch size?

### 3. Error Recovery
- What does the user see when a backend error occurs?
- Is there a retry mechanism or manual recovery path?

### 4. Data Migration
- If changing schema, how are existing records handled?
- Is backward compatibility required during rollout?

### 5. Internationalization
- Are all user-facing strings defined?
- Date/time format: which timezone?

### 6. Offline / Degraded Mode
- What happens if a dependent service is down?
- Is there a cached fallback or graceful degradation?

## How This Helps

When analyzing a PRD, scan for these items. If any are missing, add them to the gap
checklist output. This reduces back-and-forth with product by catching issues early.
