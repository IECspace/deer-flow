# Service Communication Patterns

## Context

Standard patterns used across Mirrorsphere backend services.

## Synchronous (HTTP/RPC)

- **Internal services**: Use Hertz HTTP framework with JSON payloads.
- **API naming**: `/resource/action` format (e.g., `/test/plan-case/tpc-batch-add`).
- **Timeout**: Default 10s for internal calls; 30s for calls involving external systems.
- **Retry**: At most 2 retries with exponential backoff for idempotent operations only.

## Asynchronous (Message Queue)

- **Use cases**: Notifications, async data sync, event-driven updates.
- **Pattern**: Publish event after DB commit; consumer processes independently.
- **Dead letter queue**: All async operations must have DLQ for failed messages.

## How This Helps

When generating technical review documents:
- Use these patterns as the default recommendation.
- If a PRD implies synchronous calls for heavy operations, flag it and suggest async.
- Ensure timeout and retry are specified in the API protocol section.
