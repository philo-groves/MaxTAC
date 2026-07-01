# codebase-memory-mcp Reference

`codebase-memory-mcp` is a local MCP server from DeusData. It indexes repositories into a SQLite-backed knowledge graph using tree-sitter and lightweight semantic resolution, then exposes graph, search, impact, and ADR tools to MCP clients. The MaxTAC Source plugin declares this MCP server directly and launches it through `scripts/codebase_memory_mcp.py`.

## Plugin Integration

- The Source plugin's `.mcp.json` starts `python3 scripts/codebase_memory_mcp.py serve`.
- The launcher uses `MAXTAC_CODEBASE_MEMORY_MCP` when set, then a MaxTAC-managed cache under `$CODEX_HOME/maxtac/tools/codebase-memory-mcp/`, then an existing `codebase-memory-mcp` on `PATH`, then downloads the current upstream release asset.
- Downloaded release assets are checked against the release `checksums.txt` before installation.
- The launcher does not run the upstream `install` command and does not modify global Codex, Claude, Gemini, or other agent configuration files.
- Set `MAXTAC_CODEBASE_MEMORY_NO_DOWNLOAD=1` to require an existing binary and disable first-run download.
- Set `MAXTAC_CODEBASE_MEMORY_UI=1` before first launch to cache the upstream UI variant instead of the standard binary. The UI binary can expose its 3D graph view on `localhost:9749` when started with upstream flags such as `--ui=true --port=9749`.
- Set `MAXTAC_CODEBASE_MEMORY_ARGS` to pass extra upstream flags to the MCP server on launch, for example `MAXTAC_CODEBASE_MEMORY_ARGS="--ui=true --port=9749"`.
- Upstream `CBM_*` variables still apply. Common examples are `CBM_CACHE_DIR`, `CBM_DIAGNOSTICS`, `CBM_LOG_LEVEL`, and `CBM_WORKERS`.

## Installation Boundary

- Do not run the upstream installer unless the user explicitly wants upstream agent auto-configuration. It can modify agent MCP configuration and instruction files.
- Prefer the Source plugin launcher for MaxTAC-managed use.
- If the launcher, binary, and MCP tools are unavailable, continue with MaxTAC Source workflows.

## Common MCP Tools

- `index_repository`: index a repository by absolute path.
- `list_projects`: list indexed repositories and graph sizes.
- `delete_project`: remove a project and all graph data.
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
python3 scripts/codebase_memory_mcp.py cli index_repository '{"repo_path": "/absolute/path/to/repo"}'
python3 scripts/codebase_memory_mcp.py cli get_graph_schema '{"project": "repo-name"}'
python3 scripts/codebase_memory_mcp.py cli search_graph '{"name_pattern": ".*Handler.*", "label": "Function"}'
python3 scripts/codebase_memory_mcp.py cli trace_path '{"function_name": "ProcessOrder", "direction": "both"}'
python3 scripts/codebase_memory_mcp.py cli detect_changes '{"repo_path": "/absolute/path/to/repo"}'
```

A system-level install can still be called directly:

```text
codebase-memory-mcp cli index_repository '{"repo_path": "/absolute/path/to/repo"}'
codebase-memory-mcp cli get_graph_schema '{"project": "repo-name"}'
codebase-memory-mcp cli search_graph '{"name_pattern": ".*Handler.*", "label": "Function"}'
codebase-memory-mcp cli trace_path '{"function_name": "ProcessOrder", "direction": "both"}'
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
