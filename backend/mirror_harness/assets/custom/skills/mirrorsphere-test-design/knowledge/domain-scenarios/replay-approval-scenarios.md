# Replay Approval Domain Scenarios

## Context

Replay approval is a core Mirrorsphere workflow. These scenarios must always be
considered when testing replay-related features.

## Must-Test Scenarios

### State Machine
- Task in `pending` state → can be approved.
- Task in `running` state → cannot be approved (already started).
- Task in `completed` state → cannot be approved (already done).
- Task in `failed` state → can be re-submitted but not directly approved.

### Role Checks
- QA Lead → can approve.
- Developer (task owner) → cannot approve own task.
- Viewer → cannot see approval button.

### Notification Side Effects
- Approval → task owner notified.
- Rejection → task owner notified with reason.
- Notification failure → approval still succeeds (fire-and-forget).

### Data Integrity
- Approved task: status, approver, timestamp all updated atomically.
- Approval comment persisted and visible in audit trail.
- Concurrent approval of same task → only first succeeds.

## How This Helps

When generating test cases for replay features:
- Use these as baseline scenarios even if the PRD doesn't list them all.
- Mark scenarios not covered by the PRD as "Inferred from platform rules".
- Prioritize state machine and role checks as P0.
