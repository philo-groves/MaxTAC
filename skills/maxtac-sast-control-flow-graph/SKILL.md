---
name: maxtac-sast-control-flow-graph
description: Use this skill to build and interpret static control-flow and call-graph evidence for MaxTAC SAST. Applies when a vulnerability hypothesis depends on reachability, guard dominance, path feasibility, callbacks, lock order, cleanup paths, state transitions, or source-to-sink paths across functions in source code or decompiled code.
---

# MaxTAC SAST Control-Flow Graph

Use this skill when a security hypothesis cannot be answered by reading one function in isolation. The goal is to create the smallest useful graph that proves or disproves reachability, ordering, and guard coverage for a targeted hypothesis.

## Operating Rules

- Build graphs around a question, not around the entire program.
- Include only nodes needed to reason about entrypoints, guards, state changes, calls, sinks, error paths, callbacks, locks, and cleanup.
- Prefer real compiler, language-server, decompiler, or analysis-tool facts over hand-drawn guesses.
- Preserve the commands, scripts, or manual steps used to derive graph facts when the graph supports a finding.
- Treat generated graphs as evidence aids. Still verify important edges by reading code or decompiled output.

## Use Cases

- Decide whether an external entrypoint can reach a dangerous sink.
- Check whether an authorization, entitlement, bounds, type, or lifetime guard dominates every sink.
- Compare success and error paths for cleanup, ownership, or partially initialized state.
- Follow callbacks, async jobs, timers, work queues, signal handlers, event listeners, or IPC replies.
- Understand state-machine transitions, one-time actions, replay paths, approval flows, and rollback behavior.
- Resolve whether a lock, reference, handle, or object remains valid across a call chain.
- Prepare concise evidence for a targeted auditor or debate prompt.

## Graph Workflow

1. Define the graph question.
   - Phrase it as a binary or bounded question: "Can unauthenticated route X reach sink Y without guard Z?"
   - Name the entrypoint, sink, guard, actor, and security invariant from `maxtac-sast-surface-triage`.

2. Select the graph type.
   - Use a call graph for caller/callee reachability.
   - Use an intra-procedural CFG for branch ordering, loops, cleanup labels, and guard dominance inside one function.
   - Use an inter-procedural path graph for multi-function source-to-sink reasoning.
   - Use a state graph for workflow transitions, approval gates, idempotency, replay, and object lifecycle.
   - Use a lock or ownership graph for concurrency and lifetime hypotheses.

3. Collect facts.
   - Start with `rg` to find entrypoints, sinks, guard functions, state fields, callbacks, and tests.
   - Use language-aware tools when available: compiler AST dumps, language servers, static analyzers, OpenGrep, code indexes, or framework route maps.
   - For binaries or apps without source, use MaxTAC RE skills to obtain xrefs, call graphs, decompiled functions, switch tables, and data references.
   - For Android, use JADX for decompiled Java/Kotlin-style flow and resource-driven entrypoints.
   - For native binaries, use Ghidra or Radare2 for xrefs, basic blocks, decompiler output, and callgraph exports.

4. Reduce the graph.
   - Keep nodes that affect security reasoning: entrypoint, sanitizer, parser, authorization check, type check, allocation, copy, state mutation, lock, reference change, callback registration, sink, cleanup, and return.
   - Collapse ordinary helper calls that do not affect control, data, state, or authority.
   - Keep uncertain edges explicit instead of silently assuming they exist.

5. Analyze dominance and feasibility.
   - Check whether the intended guard executes on all paths to the sink.
   - Check whether a value can change after validation and before use.
   - Check whether error paths skip cleanup, double cleanup, or leave partially updated state.
   - Check whether callbacks, async jobs, or reentrant calls can run under different identity, lock, or lifetime assumptions.
   - Check whether state transitions can be repeated, reordered, rolled back, or reached directly.

6. Persist the evidence.
   - For a quick pass, write a markdown path summary in the audit or research note.
   - For complex paths, persist a DOT, Mermaid, or tool-generated graph under the relevant `audits/<audit-id>/` or `research/<submodule>/artifacts/` directory.
   - Include the commands or tool steps used to derive the graph when reproducibility matters.

## Evidence Template

```markdown
## Control-Flow Evidence

- Question:
- Actor and entrypoint:
- Sink or protected transition:
- Required guard:
- Graph type:
- Tools or commands:
- Confirmed path:
- Blocking guard or missing guard:
- State, lock, or lifetime assumptions:
- Uncertain edges:
- Security conclusion:
```

## Common Graph Patterns

- Guard-dominates-sink: every path from entrypoint to sink passes the same effective guard.
- Split validation and use: validation occurs, then the checked object, path, credential, handle, or state can change before use.
- Error cleanup fork: success and failure paths free, close, release, or roll back different resources.
- Callback escape: attacker-controlled or cross-privilege callback runs after validation or while an object is partially initialized.
- State-machine bypass: code exposes a direct transition that skips an approval, payment, verification, or ownership state.
- Multi-entry invariant drift: one entrypoint enforces an invariant while another mutates the same object without the same checks.
- Reentrant edge: a callout allows attacker-controlled code to run while locks, references, or partial state are still active.

## Tool Handoff

- Use `maxtac-sast-surface-triage` before graphing to define the boundary, invariant, actor, and target slice.
- Use `maxtac-sast-opengrep` when the same graph question needs repeatable rule searches across many similar files.
- Use `maxtac-core-subagents` after graphing to send the narrowed path to an auditor such as race, memory lifetime, authorization, parser, business logic, or chain-building.
- Use DAST debugger or fuzzer skills when graph evidence leaves an edge uncertain and runtime behavior can decide it.

Good CFG work shrinks uncertainty. If the graph grows until it resembles the whole program, stop and split the question into smaller entrypoint-to-sink or state-transition paths.
