---
name: mirrorsphere-prd-analysis
description: >
  Parse PRD documents from file attachments or HTTP URLs, provide structured analysis,
  and optionally generate technical review documents on user request.
license: MIT
---

# Mirrorsphere PRD Analysis Skill

## When To Use

- The user uploads a PRD document (file attachment) or provides an HTTP URL to one.
- The user asks to analyze, decompose, or review a product requirement document.
- The user asks to generate a technical review document from a PRD.

## Inputs

Accepted input forms:

1. **File attachment** -- PRD document (PDF, Word, PPT, Excel, Markdown, text).
   Uploaded binary documents are auto-converted to `.md` in the uploads directory.
   Always read the `.md` companion (e.g., `/mnt/user-data/uploads/filename.md`)
   rather than the original binary file.
2. **HTTP URL** -- link to a PRD document (web page or file download link).
   Use the MCP tool `mirrorsphere-doc-fetch:fetch-document` to download and convert
   the URL content to readable Markdown before analysis.
3. **Inline text** -- user pastes PRD content directly in chat.

## Workflow

### Mode A: PRD Analysis (Default)

When the user provides a PRD and asks for analysis:

1. Parse the document and identify modules, features, user roles, and flows.
2. Output a structured analysis:
   - **Summary** -- one paragraph restating the PRD scope.
   - **Module decomposition** -- logical grouping of features/flows.
   - **Test point outline** -- key testable assertions per module.
   - **Gap checklist** -- missing or ambiguous items (see `assets/gap-checklist.md`).
3. Ask: *"Please review. Reply `needs revision` to adjust, or `proceed` to continue."*

### Handoff to Test Design

When the user confirms the analysis (`proceed`):

1. Output the confirmed analysis as a `requirement_model` JSON structure (with `prd`, `modules`, `requirements`, `gaps`, `assumptions` keys).
2. Route to the `mirrorsphere-test-design` Skill for test case generation.
3. The test design skill will call the `mirrorsphere-test-design:generate-cases` MCP tool with this model.

### Mode B: Technical Review Document Generation

When the user asks to generate a technical review / implementation document:

1. Parse the PRD to understand the full scope.
2. Generate a structured technical review document containing the sections defined below.
3. Present the document to the user for review.
4. Iterate if the user requests changes.

## Technical Review Document Structure

When generating a technical review document, include these sections:

### 1. Overview

- Background and objectives.
- Scope of change (affected systems, services, pages).
- Related PRD reference.

### 2. Architecture Changes

- System architecture diagram (Mermaid `flowchart`) showing affected components.
- New services, modules, or dependencies introduced.
- Impact on existing architecture (upstream/downstream effects).

### 3. API Protocol

For each new or modified API endpoint:

| Field | Content |
|-------|---------|
| Endpoint | Path and method |
| Request | JSON schema with field descriptions |
| Response | JSON schema with field descriptions |
| Error codes | Relevant error conditions |
| Auth | Authentication/authorization requirements |

### 4. Flow Diagrams

- Core business flow (Mermaid `sequenceDiagram` or `flowchart`).
- Exception/error handling flow.
- State transitions (if stateful operations involved).

### 5. Database Design

For each new or modified table:

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ... | ... | ... | ... |

Include:
- Index design and query patterns.
- Migration strategy (new table vs alter existing).
- Data volume estimation.

### 6. Key Technical Changes

- Core logic changes and their rationale.
- Algorithm or business rule implementations.
- Third-party service integrations.
- Configuration changes.

### 7. Security & Compliance

- Authentication and authorization checks.
- Input validation and sanitization.
- Sensitive data handling (PII, encryption, masking).
- Rate limiting or abuse prevention.
- Audit logging requirements.

### 8. Non-Functional Considerations

- Performance targets (latency, throughput, concurrency).
- Scalability approach (horizontal/vertical, caching strategy).
- Monitoring and alerting (metrics, dashboards, alerts).
- Rollback strategy and feature flags.

### 9. Test Strategy

- Unit test coverage targets.
- Integration test scope.
- Key scenarios to validate (link to `mirrorsphere-test-design` for detailed cases).

### 10. Timeline & Risk

- Implementation milestones.
- Dependencies and blockers.
- Known risks and mitigation plans.

## Human-in-the-Loop (Mandatory)

- **Never** assume technical decisions without evidence from the PRD.
- For ambiguous requirements, flag them as gaps and ask the user before making assumptions.
- Label inferred technical choices clearly: "Recommended based on context: ...".
- When generating architecture or DB design, present options if multiple approaches exist.

## Grounding Rules

- Generate only from the provided document content.
- Do not invent product requirements or business rules.
- Technical recommendations must be justified by the PRD scope.
- If the PRD lacks sufficient detail for a section, state what information is needed.

## Knowledge Base

The `knowledge/` directory contains accumulated domain knowledge that improves output quality:

- `knowledge/business-rules/` -- domain business rules and constraints to validate PRDs against.
- `knowledge/architecture-patterns/` -- proven patterns to recommend in technical reviews.
- `knowledge/common-gaps/` -- frequently missed items to proactively check.
- `knowledge/tech-standards/` -- team conventions that technical reviews must follow.

Read relevant knowledge files before generating output. The more knowledge accumulated,
the more aligned the output is with team standards and past decisions.

## References

- `references/prd-analysis-guide.md` -- analysis methodology.
- `references/tech-review-guide.md` -- technical document generation guidelines.
- `references/examples/sample-prd-analysis.md` -- analysis output example.
- `references/examples/sample-tech-review.md` -- technical review document example.
- `assets/gap-checklist.md` -- gap identification template.
