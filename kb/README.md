---
type: knowledge-base-index
name: nifty-ai-kb
version: 0.1.0
audience: ai-agents
---

# Nifty.AI Knowledge Base

This directory is model-agnostic context for AI coding agents. It is not a replacement for human documentation in `docs/`; it is a compact continuation graph for future development sessions.

## Directory Contract

- `project.md`: mission, non-goals, and safety constraints.
- `architecture.md`: module map, dependency boundaries, and ownership.
- `graph.md`: dependency graph and common change paths.
- `memory.md`: verified implementation facts and gotchas.
- `workflows.md`: repeatable dev/test/run workflows.
- `standards.md`: Markdown/frontmatter standards for agents, skills, hooks.
- `agents/`: reusable role prompts for AI engineering agents.
- `skills/`: task-specific procedural checklists.
- `hooks/`: event/check hooks that agents should run at key points.

## Usage Guidance

Read `project.md`, `architecture.md`, and `memory.md` before modifying code. Use `graph.md` to identify blast radius. Use skills/hooks when a task touches trading safety, API surfaces, or release packaging.
