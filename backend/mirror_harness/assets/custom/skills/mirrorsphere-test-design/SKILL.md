---
name: mirrorsphere-test-design
description: >
  Generate structured test cases from PRD documents or technical review documents
  (uploaded files or HTTP URLs), present them for user review and refinement,
  then batch-insert confirmed cases into the test plan via MCP.
license: MIT
---

# Mirrorsphere Test Design Skill

## When To Use

- The user uploads a PRD document or technical review document (file attachment).
- The user provides an HTTP URL to a PRD or technical review document.
- The user explicitly requests test case generation from requirement context.

## Inputs

Accepted input forms:

1. **File attachment** -- PRD or technical review document (PDF, Word, PPT, Excel, Markdown, text).
   Uploaded binary documents are auto-converted to `.md` in the uploads directory.
   Always read the `.md` companion (e.g., `/mnt/user-data/uploads/filename.md`)
   rather than the original binary file.
2. **HTTP URL** -- link to a PRD or technical review document (web page or file download link).
   Use the MCP tool `mirrorsphere-doc-fetch:fetch-document` to download and convert
   the URL content to readable Markdown before analysis.
3. **Inline text** -- user pastes requirement content directly in chat.

## Output Format

Generate test cases as a **table** with these columns:

| Column | Description | Notes |
|--------|-------------|-------|
| Case Name | Descriptive name of the test case | Required |
| Priority | P0 / P1 / P2 / P3 | Required |
| Precondition | State required before execution | Can be empty |
| Steps | Numbered action sequence | Required |
| Expected Result | Observable outcome | Required |
| Actual Result | Left **empty** at generation time | Always empty |
| Remark | Additional notes | Can be empty |

### Priority Definitions

- **P0**: Core flow; blocks release if broken.
- **P1**: Important functionality; workaround may exist.
- **P2**: Secondary scenario; low frequency or minor impact.
- **P3**: Edge case; cosmetic or rarely triggered.

## Workflow

### Phase 1: Parse & Generate

1. Read the PRD / technical review document from the provided source.
2. Identify modules, features, and sub-features.
3. Generate test cases covering: happy path, exception, boundary, and permission scenarios.
4. Present the full case table to the user.
5. Ask: *"Please review. Reply `needs revision` to adjust, or `confirm and submit` to insert into the test plan."*

### Phase 2: Iterate (if needed)

- User says `needs revision` → accept specific changes (add/remove/modify cases), regenerate the table, ask again.
- Repeat until user is satisfied.

### Phase 3: Generate via MCP

Once user says `confirm and submit`:

1. Construct the `requirement_model` JSON from the confirmed analysis (PRD structure with modules, requirements, gaps, assumptions).
2. Call MCP tool `mirrorsphere-test-design:generate-cases` with the requirement_model and selected profile.
3. Present the returned `summary_md` to the user for final review.
4. If user requests changes, adjust the requirement_model and call `generate-cases` again.
5. Optionally call `mirrorsphere-test-design:diff-cases` to show changes from a previous generation.

### Phase 4: Submit to Portal

Once user confirms the generated cases:

1. Ask the user for the **module_id**（模块 ID）to insert cases into. If unknown, ask the user for the module name, then call `mirrorsphere-portal_get_api_module` with `type=5` and the user-provided `name` to locate it. Confirm the returned module_id with the user before proceeding.
2. Map each case from the `cases` JSON to the batch-add API format (see `references/api-mapping.md`).
3. Call the `mirrorsphere-portal_batch_create_test_plan_case` MCP tool with the mapped cases array. Note: the `label` field in each case must be a **list of strings** (e.g., `["P0"]` or `[]`), not a single string.
4. Report the result (success count, any failures).

## Human-in-the-Loop (Mandatory)

- **Never** submit cases to the database without explicit user confirmation.
- **Never** guess module_id; always confirm with the user.
- After submission, report the API response and ask if further action is needed.

## Grounding Rules

- Generate cases only from the provided document content; do not invent requirements.
- If the document is ambiguous, flag the gap and ask the user to clarify before generating cases for that section.
- Label inferred scenarios clearly: "Inferred from context: ...".

## Knowledge Base

The `knowledge/` directory contains accumulated testing knowledge that improves coverage:

- `knowledge/test-strategies/` -- reusable strategies for common feature types (batch, CRUD, async).
- `knowledge/domain-scenarios/` -- must-test scenarios for Mirrorsphere domain features.
- `knowledge/regression-patterns/` -- past bugs and the test cases that would have caught them.
- `knowledge/platform-conventions/` -- coverage standards, naming rules, priority distribution.

Read relevant knowledge files before generating test cases. Historical patterns help ensure
coverage of edge cases that are easy to miss without domain experience.

## References

- `references/api-mapping.md` -- field mapping between output table and MCP API.
- `references/test-design-guide.md` -- methodology and scenario classification.
- `references/examples/sample-test-cases.md` -- full worked example.
- `assets/case-template.md` -- single test case structure.
