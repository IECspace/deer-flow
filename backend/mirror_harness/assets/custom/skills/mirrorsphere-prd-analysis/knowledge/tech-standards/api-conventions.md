# API Conventions

## Context

Team-wide conventions for Mirrorsphere backend API design.

## Naming

- Endpoint format: `/resource/action` (e.g., `/test/plan-case/tpc-add`).
- Use lowercase with hyphens for URL paths.
- Prefix with resource domain: `/test/`, `/record/`, `/replay/`, `/mock/`.

## Request/Response

- Content-Type: `application/json` for all non-file endpoints.
- Response envelope:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {},
    "time": 1700000000
  }
  ```
- `code: 0` means success; non-zero is error.
- Error codes: 6-digit, first 3 = domain, last 3 = specific error.

## Pagination

- Query params: `page` (1-based) and `page_size` (default 20, max 1000).
- Response includes: `total`, `list`, `page`, `page_size`.

## Authentication

- All endpoints require valid session token in header.
- Role-based access: checked at handler layer before business logic.

## How This Helps

When generating technical review documents:
- Follow these conventions for any new API design.
- Flag deviations from these conventions as review comments.
- Use the standard response envelope in all API protocol sections.
