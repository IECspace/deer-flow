# PRD Analysis Guide

## Purpose

Transform a PRD into a structured, test-ready decomposition that a test-design skill can consume.

## Steps

### 1. Scope Identification

- Identify the product area, affected modules, and user roles.
- Confirm boundaries: what is in scope vs. explicitly out of scope.

### 2. Module Decomposition

- Break the PRD into logical modules or user flows.
- Each module should map to a testable unit (a page, an API, a workflow).

### 3. Test Point Extraction

For each module, extract:

- **Happy path assertions** -- the core behavior described in the PRD.
- **Exception scenarios** -- error states, invalid inputs, timeout handling.
- **Boundary conditions** -- limits, pagination, max lengths, edge values.
- **Permission checks** -- role-based access, visibility rules.
- **Data constraints** -- required fields, formats, uniqueness, referential integrity.

### 4. Gap Identification

Use the checklist in `../assets/gap-checklist.md` to scan for:

- Missing acceptance criteria.
- Undefined user roles or personas.
- Unspecified error handling behavior.
- Absent non-functional requirements (performance, security, accessibility).
- Ambiguous state transitions or flow branches.

### 5. Output Assembly

Combine the above into the standard output format defined in `SKILL.md`:
summary, module decomposition, test point outline, gap checklist, confirmation prompt.

## Handoff to Test Design

Once the user confirms `proceed to generate`:

- Pass the confirmed module list and test points to `mirrorsphere-test-design`.
- Include any user-supplied supplements collected during iteration.
- The test-design skill uses this as its input scope -- no additional PRD re-reading required.
