---
name: mirrorsphere-mindmap-generation
description: >
  Generate Mermaid test mindmaps from agreed test-design scope;
  only after user confirmation when the request started from a PRD.
license: MIT
---

# Mirrorsphere Mindmap Generation Skill

## When To Use

- The user wants a visual mindmap of test scenarios for review.
- Best after test points or cases are agreed; must stay consistent with the confirmed scope.
- Can be used standalone when the user provides a module/scenario list directly.

## Human-in-the-Loop (Mandatory)

1. **Validate**: Mindmap nodes must match the confirmed scope -- no extra branches from invented requirements.
2. **Confirm**: If the session started as PRD -> test -> mindmap and the user has not yet said `proceed to generate`, follow the same review gate as the other skills.
3. **Iterate**: If the user changes scope, regenerate the mindmap and state what changed.

## Output Format

- Default to `flowchart LR` for reliable left-to-right rendering across tools.
- Only use `mindmap` directive if the renderer is confirmed to support direction control.
- Keep node labels short (under 40 characters).
- Group by module at the first level, then by scenario type at the second level.

## Layout Rules

```
flowchart LR
  Root[Feature Name]
  Root --> Module1[Module A]
  Root --> Module2[Module B]
  Module1 --> Happy1[Happy: scenario]
  Module1 --> Exc1[Exception: scenario]
  Module2 --> Happy2[Happy: scenario]
```

## References

- `references/examples/sample-mindmap.md` -- worked example with Mermaid code.
