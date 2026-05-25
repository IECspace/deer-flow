# Sample Test Cases

## Input

PRD excerpt: "Add batch replay approval for test environments. QA Lead can select up to 50 pending replay tasks and approve them in one action. If any task fails validation, the entire batch is rejected."

## Generated Test Case Table

| Case Name | Priority | Precondition | Steps | Expected Result | Actual Result | Remark |
|-----------|----------|--------------|-------|-----------------|---------------|--------|
| Batch approve 5 valid tasks | P0 | User is QA Lead; 5 pending tasks exist | 1. Navigate to replay list\n2. Select 5 pending tasks\n3. Click Batch Approve | All 5 tasks approved; success notification shown | | Core happy path |
| Batch approve at max limit (50) | P1 | 50+ pending tasks visible | 1. Select exactly 50 tasks\n2. Click Batch Approve | All 50 tasks approved successfully | | Boundary: max batch size |
| Exceed 50 task selection limit | P1 | 51+ pending tasks visible | 1. Attempt to select 51 tasks | Submit button disabled; warning: "Maximum 50 tasks" | | Boundary: over limit |
| One task fails validation in batch | P0 | 1 of 5 selected tasks has invalid state | 1. Select 5 tasks (1 invalid)\n2. Click Batch Approve | Entire batch rejected; error shows which task failed | | Exception: atomic rejection |
| Non-QA-Lead attempts batch approve | P0 | User has Developer role | 1. Navigate to replay list\n2. Attempt Batch Approve | 403 Forbidden; action not available | | Permission check |
| Select non-pending task | P2 | Mix of pending and completed tasks | 1. Attempt to check a completed task | Checkbox disabled for non-pending tasks | | UI guard |
| Empty selection submitted | P3 | No tasks selected | 1. Click Batch Approve with nothing selected | Button disabled or error: "No tasks selected" | | Edge case |
| Notification sent to task owners | P1 | Batch approved successfully | 1. Check notification inbox of each task owner | Each owner receives one notification with task ID and approver | | Side effect |

## After User Confirms

API payload sent to `/test/plan-case/tpc-batch-add`:

```json
{
  "cases": [
    {
      "module_id": 42,
      "name": "Batch approve 5 valid tasks",
      "level": 1,
      "precondition": "User is QA Lead; 5 pending tasks exist",
      "steps": "1. Navigate to replay list\n2. Select 5 pending tasks\n3. Click Batch Approve",
      "expected_result": "All 5 tasks approved; success notification shown",
      "actual_result": "",
      "label": "P0",
      "remark": "Core happy path",
      "import_pool": false
    },
    {
      "module_id": 42,
      "name": "Non-QA-Lead attempts batch approve",
      "level": 1,
      "precondition": "User has Developer role",
      "steps": "1. Navigate to replay list\n2. Attempt Batch Approve",
      "expected_result": "403 Forbidden; action not available",
      "actual_result": "",
      "label": "P0",
      "remark": "Permission check",
      "import_pool": false
    }
  ]
}
```
