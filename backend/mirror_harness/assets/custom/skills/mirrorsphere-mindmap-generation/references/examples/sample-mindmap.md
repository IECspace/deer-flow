# Sample Mindmap

## Context

Generated from the "Batch Replay Approval" test design scope.

## Mermaid Code

```mermaid
flowchart LR
  Root[Batch Replay Approval]

  Root --> UI[Batch Selection UI]
  Root --> API[Batch Approval API]
  Root --> Notif[Notification]

  UI --> UI_H[Happy: select 5 tasks]
  UI --> UI_B[Boundary: exceed 50 limit]
  UI --> UI_E[Exception: non-pending blocked]

  API --> API_H[Happy: full batch approved]
  API --> API_E1[Exception: partial validation fail]
  API --> API_P[Permission: non-QA-Lead rejected]
  API --> API_B[Boundary: empty array]

  Notif --> Notif_H[Happy: owners notified]
```

## Rendering Notes

- Use `flowchart LR` for guaranteed left-to-right layout.
- First level: modules (match PRD analysis decomposition).
- Second level: scenarios prefixed with type (Happy/Exception/Boundary/Permission).
- Keep labels under 40 characters for readability.
