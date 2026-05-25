# Approval Flow Business Rules

## Context

Mirrorsphere platform has multiple approval flows (record approval, replay approval).
These rules apply across all approval features.

## Rules

1. **Dual-role separation**: The submitter of a task cannot approve their own submission.
2. **Approval timeout**: Pending approvals expire after 72 hours; task returns to draft state.
3. **Batch limit**: Any batch operation is capped at 50 items to prevent accidental mass actions.
4. **Audit trail**: Every approval/rejection must be logged with operator, timestamp, and reason.
5. **Notification**: Approval result must notify the task owner within 5 seconds (async acceptable).

## How This Helps

When analyzing a PRD that involves approval:
- Check if the PRD specifies who cannot approve (rule 1).
- Flag if timeout behavior is missing (rule 2).
- Validate batch limits if batch operations are mentioned (rule 3).
- Ensure audit and notification are addressed (rules 4-5).
