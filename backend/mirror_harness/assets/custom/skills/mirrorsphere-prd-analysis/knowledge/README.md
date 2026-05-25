# PRD Analysis Knowledge Base

This directory contains accumulated domain knowledge that improves the quality and
efficiency of PRD analysis and technical review document generation.

## Directory Structure

```
knowledge/
├── README.md                  ← You are here
├── business-rules/            ← Domain business rules and constraints
├── architecture-patterns/     ← Proven architecture patterns for this platform
├── common-gaps/               ← Frequently missed items in PRDs
└── tech-standards/            ← Team technical standards and conventions
```

```
┌────────────────────────┬────────────────┬────────────────────────────┐
│         子目录         │      用途      │         Demo 文件          │
├────────────────────────┼────────────────┼────────────────────────────┤
│ business-rules/        │ 业务规则约束   │ approval-flow-rules.md     │
├────────────────────────┼────────────────┼────────────────────────────┤
│ architecture-patterns/ │ 技术架构模式   │ service-communication.md   │
├────────────────────────┼────────────────┼────────────────────────────┤
│ common-gaps/           │ PRD 常见遗漏项 │ frequently-missed-items.md │
├────────────────────────┼────────────────┼────────────────────────────┤
│ tech-standards/        │ 团队技术规范   │ api-conventions.md         │
└────────────────────────┴────────────────┴────────────────────────────┘
```

## How To Use

The skill reads files in this directory as background knowledge when analyzing PRDs
or generating technical reviews. The more relevant knowledge accumulated here, the
more precise and team-aligned the output becomes.

## How To Maintain

- **Add** a new `.md` file under the appropriate subdirectory when you identify a
  pattern, rule, or standard that should be reused in future analyses.
- **Update** existing files when rules change or evolve.
- **Remove** files that are no longer applicable.
- File names should be descriptive: `approval-flow-rules.md`, not `note1.md`.

## Categories

### business-rules/
Domain-specific rules that constrain how features work.
Examples: approval chains, role permissions, data lifecycle, billing logic.

### architecture-patterns/
Proven patterns used in this platform that guide technical review generation.
Examples: service communication patterns, caching strategies, queue usage, DB sharding.

### common-gaps/
Frequently missed items in PRDs from past experience.
Examples: recurring ambiguities, fields always forgotten, edge cases always missed.

### tech-standards/
Team conventions and coding standards that technical reviews should respect.
Examples: API naming rules, error code conventions, logging standards, test coverage targets.
