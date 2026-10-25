---
type: standards
name: kb-authoring-standards
---

# Knowledge Base Authoring Standards

All `kb/**/*.md` files should be model-agnostic and concise enough for future AI agents to read quickly.

## Frontmatter

Use YAML frontmatter with at least:

```yaml
---
type: <project-brief|architecture-notes|agent|skill|hook|workflow-guide>
name: <stable-slug>
---
```

## Agent Files

Agent files describe role, responsibilities, tools, constraints, and expected outputs. They should not mention a specific model vendor.

## Skill Files

Skill files describe when to use the skill, ordered steps, verification, and failure modes.

## Hook Files

Hook files describe event triggers and required checks. They are checklists, not executable scripts.

## Human Docs Boundary

`docs/` is for product/design/setup documentation written for humans. `kb/` is for compressed operational memory and continuation context for agents.
