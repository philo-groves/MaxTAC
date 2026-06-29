# codebase-memory-mcp Reference

`codebase-memory-mcp` is an external local MCP server from DeusData. It indexes repositories into a SQLite-backed knowledge graph using tree-sitter and lightweight semantic resolution, then exposes graph, search, impact, and ADR tools to MCP clients.

## Installation Boundary

- Do not install or run installer scripts unless the user approves. The upstream installer can modify agent MCP configuration and instruction files.
- If installation is approved, prefer the upstream release or installer and let the user choose whether to install the UI variant.
- If installation is not approved or the binary is unavailable, continue with MaxTAC Source workflows.

## Common MCP Tools

- `index_repository`: index a repository by absolute path.
- `list_projects`: list indexed repositories and graph sizes.
- `index_status`: check whether a repository is indexed or stale.
- `get_graph_schema`: inspect graph labels, edge types, and properties.
- `get_architecture`: summarize languages, packages, entrypoints, routes, hotspots, boundaries, layers, clusters, and ADRs.
- `search_graph`: find nodes by label, name pattern, file pattern, and degree filters.
- `trace_path`: trace inbound, outbound, or both-direction call paths for a function.
- `detect_changes`: map git changes to affected symbols and blast radius.
- `query_graph`: run bounded read-only Cypher-like queries.
- `get_code_snippet`: retrieve code for a qualified symbol; read the source file before relying on it.
- `search_code`: grep-like search over indexed files.
- `manage_adr`: create, read, update, and delete Architecture Decision Records.
- `ingest_traces`: ingest runtime traces to validate route/call edges.

## CLI Fallback

Every MCP tool can be invoked through the CLI when the binary is installed:

```text
codebase-memory-mcp cli index_repository '{"repo_path": "C:/absolute/path/to/repo"}'
codebase-memory-mcp cli get_graph_schema '{"project": "repo-name"}'
codebase-memory-mcp cli search_graph '{"name_pattern": ".*Handler.*", "label": "Function"}'
codebase-memory-mcp cli trace_path '{"function_name": "ProcessOrder", "direction": "both"}'
codebase-memory-mcp cli detect_changes '{"repo_path": "C:/absolute/path/to/repo"}'
```

Use absolute paths for repository indexing. Use `list_projects` when the project name is unclear.

## Graph Artifact Policy

The project can create `.codebase-memory/graph.db.zst` as a team-shared graph snapshot. In security research, this file may disclose repository structure and symbol names. Treat it as opt-in:

- Do not commit it by default.
- Add `.codebase-memory/` to the target repository's `.gitignore` if the user wants local-only indexes.
- If the user wants a shared graph artifact, note that it is a generated binary index and should not be edited manually.

## MaxTAC Interpretation

- Codebase memory answers "where should I look?" faster than raw file exploration.
- MaxTAC still owns the security reasoning: actor, boundary, invariant, reachability, impact, proof, and reporting.
- Graph results are supporting evidence until source or runtime verification confirms the security-relevant edge.
