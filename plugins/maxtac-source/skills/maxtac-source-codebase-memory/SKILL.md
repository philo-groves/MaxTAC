---
name: maxtac-source-codebase-memory
description: "Use this skill when MaxTAC Source can use an installed codebase-memory-mcp server or CLI for source-code repository indexing, architecture overview, structural search, call-path tracing, diff impact mapping, ADR lookup, or code graph evidence before SAST triage, CFG work, OpenGrep authoring, or source scans."
---

# MaxTAC Source Codebase Memory

Use this skill as an optional structural-memory layer for source repositories. `codebase-memory-mcp` can index a repo into a local graph and answer architecture, symbol, route, call-path, diff-impact, and ADR questions quickly. Treat it as a discovery accelerator and evidence index, not as proof by itself.

Read `references/codebase-memory-mcp.md` when installation, CLI fallback, tool names, or graph artifact policy matter.

## Operating Rules

- Use codebase-memory only when the MCP tools are already available, the `codebase-memory-mcp` CLI is already installed, or the user explicitly approves installation/config changes.
- Do not make MaxTAC Source depend on this MCP. If unavailable, continue with `rg`, Source triage, OpenGrep, CFG, language servers, and domain tools.
- Prefer the graph for orientation and path selection; verify security-relevant edges by reading source, generated code, decompiler output, tests, or runtime evidence.
- Keep graph query output as artifact evidence. Rewrite durable architecture, invariants, ownership, and negative findings into the stable Core `research/` library.
- Do not commit `.codebase-memory/graph.db.zst` or other shared graph artifacts unless the user explicitly wants a team-shared index and understands it may reveal repository structure.
- Do not store secrets, tokens, proprietary snippets, or sensitive source extracts in ADRs or MaxTAC packets beyond the minimum proof required.

## Workflow

1. Establish availability.
   - If MCP tools are exposed, use them directly.
   - If only the CLI is available, use `codebase-memory-mcp cli <tool> '<json>'`.
   - If neither is available, record that codebase memory was unavailable and fall back.

2. Index or refresh the target.
   - Run `index_status` or `list_projects` first when available.
   - Run `index_repository` with an absolute repository path when the target is not indexed or is stale.
   - For CLI fallback:

```text
codebase-memory-mcp cli index_repository '{"repo_path": "C:/absolute/path/to/repo"}'
codebase-memory-mcp cli index_status '{"repo_path": "C:/absolute/path/to/repo"}'
```

3. Get orientation before broad reading.
   - Use `get_graph_schema` for available labels and relationships.
   - Use `get_architecture` for languages, packages, routes, hotspots, boundaries, layers, clusters, and ADR summary.
   - Save only the parts that shape the current security question.

4. Query narrowly.
   - Use `search_graph` to find symbols, routes, resources, and files.
   - Use `trace_path` for caller/callee paths around entrypoints, guards, sinks, and dangerous state transitions.
   - Use `search_code` for indexed text search when it can reduce raw `rg` noise.
   - Use `query_graph` only for bounded read-only questions; keep Cypher queries small and explain what security question they answer.
   - Use `get_code_snippet` only as a pointer, then read the actual file before relying on details.

5. Map changes when reviewing diffs.
   - Use `detect_changes` to identify affected symbols, blast radius, and risk classifications.
   - Convert useful results into Source Scan supporting context, not automatic findings.

6. Manage architecture memory carefully.
   - Use `manage_adr` to read existing ADRs when they explain security boundaries.
   - Create or update ADRs only for real architecture decisions the user wants in the codebase-memory store.
   - MaxTAC’s durable research library remains the canonical security notebook; ADRs are a code-intelligence cache, not a replacement for `research/`.

## Security Handoff

Use this compact packet when graph results shape SAST triage, CFG, OpenGrep, auditors, or Source Scan rows:

```markdown
## Codebase Memory Packet

- Target repository:
- Index status:
- Architecture facts used:
- Symbols/routes/resources queried:
- Query tools and parameters:
- Candidate entrypoints:
- Candidate guards:
- Candidate sinks or protected transitions:
- Confirmed graph edges:
- Edges requiring source verification:
- Diff impact or blast radius:
- ADRs consulted:
- Security hypothesis or negative conclusion:
- Next workflow: Surface Triage / CFG / OpenGrep / Source Scan / Auditor
```

## Tool Handoff

- Use `maxtac-sast-surface-triage` after architecture and symbol discovery to write the actor, boundary, invariant, and candidate hypothesis.
- Use `maxtac-sast-control-flow-graph` when graph edges must be reduced into a security path with guard dominance, state, lock, callback, or cleanup reasoning.
- Use `maxtac-sast-opengrep` when a codebase-memory query identifies a pattern that should become a repeatable search.
- Use `maxtac-source-scan` when `detect_changes` or graph orientation informs a bounded diff, repo, or scoped source review.
- Use `maxtac-core-subagents` only after graph findings are converted into a focused packet and verified against source where it matters.

## Failure Modes

- Graph staleness: re-check `index_status` or re-index before relying on changed files.
- False edges or missing edges: tree-sitter and lightweight semantic analysis can miss dynamic dispatch, reflection, generated routes, dependency injection, macro expansion, framework magic, and runtime registration.
- Overbroad architecture dumps: summarize only the facts needed for the current security question.
- Memory drift: do not let ADRs, graph artifacts, and MaxTAC research notes diverge. If a conclusion matters to security research, rewrite it into `research/`.
