# Test Design Knowledge Base

This directory contains accumulated testing knowledge that improves the quality,
coverage, and efficiency of test case generation.

## Directory Structure

```
knowledge/
├── README.md                  ← You are here
├── test-strategies/           ← Proven test strategies for different feature types
├── domain-scenarios/          ← Domain-specific scenarios that must always be tested
├── regression-patterns/       ← Known regression patterns from past incidents
└── platform-conventions/      ← Platform-specific testing conventions
```

```
┌───────────────────────┬───────────────────┬──────────────────────────────┐
│        子目录         │       用途        │          Demo 文件           │
├───────────────────────┼───────────────────┼──────────────────────────────┤
│ test-strategies/      │ 可复用测试策略    │ batch-operations.md          │
├───────────────────────┼───────────────────┼──────────────────────────────┤
│ domain-scenarios/     │ 领域必测场景      │ replay-approval-scenarios.md │
├───────────────────────┼───────────────────┼──────────────────────────────┤
│ test-strategies/      │ 可复用测试策略    │ batch-operations.md          │
├───────────────────────┼───────────────────┼──────────────────────────────┤
│ domain-scenarios/     │ 领域必测场景      │ replay-approval-scenarios.md │
├───────────────────────┼───────────────────┼──────────────────────────────┤
│ regression-patterns/  │ 历史 bug 回归模式 │ double-approval-bug.md       │
├───────────────────────┼───────────────────┼──────────────────────────────┤
│ platform-conventions/ │ 平台测试规范      │ test-coverage-standards.md   │
└───────────────────────┴───────────────────┴──────────────────────────────┘
```

## How To Use

The skill reads files in this directory as background knowledge when generating
test cases. Historical patterns help ensure coverage of edge cases that are easy
to miss without domain experience.

## How To Maintain

- **Add** a new `.md` file when you discover a test pattern, regression, or scenario
  that should be checked in future test designs.
- **Update** existing files when platform behavior changes.
- **Remove** files for deprecated features or obsolete patterns.
- File names should be descriptive: `replay-timeout-scenarios.md`, not `cases1.md`.

## Categories

### test-strategies/
Reusable test strategies for common feature types.
Examples: CRUD operations testing, batch operations testing, async flow testing.

### domain-scenarios/
Domain-specific test scenarios that must always be covered for Mirrorsphere features.
Examples: record/replay-specific edge cases, approval-specific checks, mock-specific validations.

### regression-patterns/
Patterns derived from past bugs or incidents. Each entry describes what went wrong
and what test case would have caught it.
Examples: race conditions that caused double-approval, timeout bugs, data consistency issues.

### platform-conventions/
Testing conventions and standards specific to this platform.
Examples: required coverage for each priority level, naming rules, how to handle async assertions.
