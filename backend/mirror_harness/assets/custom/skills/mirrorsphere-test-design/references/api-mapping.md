# API Field Mapping

## Output Table → MCP Batch-Add API

Maps the user-facing test case table to the `batch_create_test_plan_case` request payload.

### Field Mapping

| Table Column | API Field         | Type | Notes                                                             |
|--------------|-------------------|------|-------------------------------------------------------------------|
| (user-provided) | `module_id`       | int | Required. Ask user for the test plan module ID before submission. |
| Case Name | `name`            | string | Required. Use as the test case name.                              |
| Priority | `level`           | int | Map: P0→1, P1→2, P2→3, P3→4                                       |
| Precondition | `precondition`    | object | `{"text": "<content>", "attachments": []}` — put content in `text`, leave `attachments` empty. |
| Steps | `steps`           | object | `{"text": "<content>", "attachments": []}` — put steps in `text` (use `\n` for line breaks), leave `attachments` empty. |
| Expected Result | `expected_result` | object | `{"text": "<content>", "attachments": []}` — put expected result in `text`, leave `attachments` empty. |
| Actual Result | `actual_result`   | object | `{"text": "", "attachments": []}` — always empty text at generation time. |
| Remark | `remark`          | string | Direct copy.                                                      |
| -- | `label`           | list[string] | Set to priority label list (e.g. `["P0"]`) or empty list `[]`.      |
| -- | `import_pool`     | bool | Default `false` unless user requests pool import.                 |

### Priority Mapping

| User-Facing | API Value |
|-------------|-----------|
| P0 | 1 |
| P1 | 2 |
| P2 | 3 |
| P3 | 4 |

### Batch-Add Request Format

```json
{
  "cases": [
    {
      "module_id": 123,
      "name": "Case Name",
      "level": 1,
      "precondition": {"text": "Precondition content", "attachments": []},
      "steps": {"text": "Step 1\nStep 2\nStep 3", "attachments": []},
      "expected_result": {"text": "Expected result content", "attachments": []},
      "actual_result": {"text": "", "attachments": []},
      "label": ["P0"],
      "remark": "Remark content",
      "import_pool": false
    }
  ]
}
```

### MCP Tool

- Tool name: `mirrorsphere-portal_batch_create_test_plan_case`
- When `tool_search` is enabled, use the tool via LangChain tool calling mechanism.
- Auth headers (Moa-Token, Moa-Project, MS-Biz) are automatically injected by `portal_headers_interceptor`.

### Success Response

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 100001 | Parameter error |
| 100004 | Module does not exist |
| 500000 | Internal server error |

### Helper Tools

If the user doesn't know the module_id, use:

- `mirrorsphere-portal_get_api_module` — Get info by module ID or name
- `mirrorsphere-portal_list_api_modules` — List all modules as tree
- `mirrorsphere-portal_get_api_module_leaf_nodes` — Get deepest leaf modules

Auth headers are automatically injected by `portal_headers_interceptor`.
