---
name: mirrorsphere-knowledge
description: Use this skill when the user asks about Mirrorsphere platform capability, code locations, API/page relation, record-replay-mock-diff workflows, troubleshooting paths, onboarding, or implementation guidance in the Mirrorsphere repository.
license: MIT
---

# Mirrorsphere Knowledge Skill

This skill turns DeerFlow into a Mirrorsphere-focused engineering assistant.

## When To Use

Use this skill when the user asks about:

- Mirrorsphere architecture or platform capability
- code locations or which service/page handles a feature
- record / replay / mock / diff / agent / worker / airtest relations
- troubleshooting and failure path analysis
- onboarding into Mirrorsphere modules
- where to implement a change in the Mirrorsphere codebase
- **Portal-managed data details**: test case details, test suite info, execution records, module metadata, project configurations (use `mirrorsphere-portal_*` MCP tools)

## Grounding Rules

- All Mirrorsphere-related questions must be answered from Mirrorsphere internal knowledge only.
- Treat the internal knowledge boundary as: indexed repository files, `references/knowledge-pack.md`, `harness/docs/*`, `harness/README.md`, and future Mirrorsphere MCP/runtime assets.
- Do not fill gaps with generic world knowledge, public internet facts, guessed company background, founding year, product marketing copy, or outside assumptions.
- If the internal knowledge does not contain enough evidence, say that explicitly and ask the user to narrow the question to a module, file, page, API, service, or workflow.
- Prefer repository evidence over broad summaries.
- When answering implementation questions, cite concrete file paths.
- Explain inferred parts clearly, and clearly label them as inference.
- When the user asks "Mirrorsphere 是什么", "Mirrorsphere 简介", "Mirrorsphere 介绍", or similar overview questions, answer from `references/docs/overview.md` first.
- If the current Mirrorsphere knowledge sources do not contain a formal definition, say that explicitly instead of inventing company history, founding year, or external background.

## Suggested Investigation Order

1. Read `references/generated/knowledge-pack.md` for the generated module map and capability index.
2. For platform-definition questions ("what is Mirrorsphere"), read `references/docs/overview.md` first.
3. For architecture questions, read `references/docs/architecture.md`.
4. For roadmap or future-phase questions, read `references/docs/roadmap.md`.
5. Use file paths listed in the knowledge pack as entry points for implementation-aware answers.
6. For workflow questions, connect `portal`, `pilot_web`, `recorder`, `replayer`, and `airtest-agent`.
7. Distinguish confirmed facts from your inference whenever you summarize a flow.

## Key Mirrorsphere Areas

- `portal/`: backend service and business orchestration
- `pilot_web/`: frontend pages and API clients
- `recorder/`: traffic recording agent
- `replayer/`: traffic replay worker
- `airtest-agent/`: UI automation execution agent
- `harness/`: Mirrorsphere AI extension layer

## Portal Data Access (via MCP Tools)

When the user asks for **specific Portal-managed data**, use the `mirrorsphere-portal_*` MCP tools to fetch live data. Available Portal MCP tools include:

- **`mirrorsphere-portal_get_test_plan_case`** — Query test plan case information by criteria (case key, name, etc.)
- **`mirrorsphere-portal_tree_api_modules`** — Get module hierarchy for project structure
- **`mirrorsphere-portal_get_api_module`** — Get module details by ID or name
- **`mirrorsphere-portal_list_api_modules`** — List all API modules
- **`mirrorsphere-portal_batch_create_test_plan_case`** — Batch create test cases (write operation)

**Detection rule**: If the user mentions:
- A test case ID (e.g., `CASE-01KJZERV1FD8FWDGNKR8BJG29M`)
- Asks "帮我查询...", "获取...", "查看...", "有哪些..." (query/retrieve/view/list actions)
- Asks for specific Portal-managed data (cases, modules, records, configurations)

Then call the appropriate Portal tool.

**Example patterns**:
- 帮我查询接口用例 CASE-01KJZERV1FD8FWDGNKR8BJG29M 的详情 → call `mirrorsphere-portal_get_test_plan_case` with case ID
- 项目中有哪些测试模块 → call `mirrorsphere-portal_tree_api_modules` to get project structure
- 查询模块 "登录服务" 的详情 → call `mirrorsphere-portal_get_api_module` with module name

**Auth & Error Handling**: Auth headers (Moa-Token, Moa-Project, MS-Biz) are automatically injected by `portal_headers_interceptor`. If a Portal tool call fails (auth missing, server error, network issue), report the error explicitly instead of fabricating data.

## Output Rules

- For Mirrorsphere questions, never answer beyond what the internal knowledge can support.
- If evidence is weak, respond with the confirmed internal facts first, then state what is still unconfirmed.
- Cite concrete file paths whenever the question asks where logic lives.
- Prefer concise, implementation-aware answers over generic architecture prose.
- If the knowledge pack does not contain enough evidence, say that the current Mirrorsphere index needs refresh.
- When returning Portal-fetched data, cite the MCP tool call result as the authoritative source.
