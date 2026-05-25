# Gap Checklist Template

Use this checklist to systematically identify missing or ambiguous items in a PRD.

## Categories

### Roles & Permissions
- [ ] All user roles mentioned and defined
- [ ] Permission boundaries specified for each action
- [ ] Admin/superuser override behavior described

### Acceptance Criteria
- [ ] Each feature has measurable acceptance criteria
- [ ] Success and failure states explicitly defined
- [ ] Edge cases acknowledged (empty state, max load, concurrent access)

### Data Constraints
- [ ] Required vs optional fields specified
- [ ] Field formats and validation rules defined
- [ ] Uniqueness and referential integrity rules stated
- [ ] Data retention and deletion behavior described

### Error Handling
- [ ] Error responses and user-facing messages defined
- [ ] Retry and fallback behavior specified
- [ ] Partial failure handling described (atomic vs best-effort)

### Non-Functional Requirements
- [ ] Performance targets (latency, throughput) stated
- [ ] Security considerations addressed (auth, input sanitization)
- [ ] Accessibility requirements mentioned
- [ ] Scalability constraints documented

### State & Flow
- [ ] All state transitions diagrammed or listed
- [ ] Branching conditions unambiguous
- [ ] Concurrency and race condition handling described
- [ ] Undo/rollback behavior specified

## Output Format

| # | Gap Description | Category | Severity (High/Medium/Low) |
|---|-----------------|----------|---------------------------|
| 1 | ...             | ...      | ...                       |
