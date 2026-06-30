---
name: maxtac-core-corpus
description: "Use this skill when MaxTAC research needs a growable faceted knowledge base, canonical research notes, closure notes, tag and graph based retrieval, anti-tunnel orientation packs, generated research views, import of existing research markdown, or workspace corpus hygiene instead of hand-growing directory hierarchies."
---

# MaxTAC Core Corpus

Use this skill to manage durable MaxTAC research knowledge without letting the active directory become the system architecture. The corpus uses compact canonical notes under `research/notes/`, generated views under `research/views/`, raw corpus artifacts under `research/artifacts/`, and `workspace.sqlite` as the index for tags, typed graph edges, FTS search, and orientation packs.

## Storage Contract

```text
research/
  notes/       # canonical compact notes named by stable ID, for example R-000001.md
  views/       # generated maps and indexes; safe to overwrite
  artifacts/   # raw imported markdown, transcripts, and evidence that is not durable prose
```

Use `scripts/corpus.py` instead of creating new research subdirectories by hand. Directories become generated views, not the source of truth.

## Workflow

1. Run `init` when a workspace starts or when adopting the corpus in an existing workspace.
2. Before writing durable research, run `orient` for the target query or tag set. Read matching notes, graph neighbors, negative knowledge, and open questions first.
3. Add compact notes with `add-note`. Every note needs a kind, status, summary, body, and facet tags.
4. Use graph edges with `link` when a note refines, contradicts, supersedes, supports, depends on, or closes another note.
5. Run `compile-views` after meaningful writes so humans can browse generated indexes without hand-maintaining a hierarchy.
6. Run `lint` before handoff, report drafting, or long branch continuation.

For tiny non-reportable targets using MaxTAC thin closure, write exactly one compact `closure` or `negative-result` note unless new reusable architecture was discovered. Point it at the result contract, source receipt, and caller/runtime proof artifact; do not restate the same conclusion into separate narrative packets.

## Commands

Initialize:

```text
python3 <skill-dir>/scripts/corpus.py init --root <workspace-root>
```

Create a note:

```text
python3 <skill-dir>/scripts/corpus.py add-note --root <workspace-root> \
  --title "Tenant export authorization model" \
  --kind architecture \
  --status observed \
  --summary "The export service checks tenant membership before object reads; retry behavior is still unknown." \
  --tag domain=web --tag subsystem=export-api --tag boundary=tenant --tag knowledge-kind=architecture \
  --evidence research/notes/R-000001.md \
  --body "Synthesized note body..."
```

Import existing markdown:

```text
python3 <skill-dir>/scripts/corpus.py import-file --root <workspace-root> research/old/export.md \
  --kind architecture \
  --status draft \
  --tag subsystem=export-api --tag boundary=tenant --tag knowledge-kind=architecture
```

Link notes:

```text
python3 <skill-dir>/scripts/corpus.py link --root <workspace-root> R-000002 refines R-000001 \
  --status observed --confidence medium --evidence research/notes/R-000002.md
```

Search and orient:

```text
python3 <skill-dir>/scripts/corpus.py search --root <workspace-root> --query "tenant export guard"
python3 <skill-dir>/scripts/corpus.py orient --root <workspace-root> --query "tenant export guard" --diversify-by subsystem,boundary,knowledge-kind
```

Compile views and lint:

```text
python3 <skill-dir>/scripts/corpus.py compile-views --root <workspace-root>
python3 <skill-dir>/scripts/corpus.py lint --root <workspace-root> --strict
```

## Note Rules

- Keep each note compact. Split notes over about 220 lines; the helper rejects notes over 320 lines.
- Use at least two facet tags. Include one of `subsystem`, `boundary`, `asset`, or `knowledge-kind`.
- Use `observed`, `confirmed`, `negative`, `stale`, `superseded`, or `artifact-only` only with evidence.
- Keep raw tool output, transcripts, and imported legacy markdown under `research/artifacts/` unless rewritten into compact durable prose.
- Prefer `update-note` or `link` over adding a near-duplicate note.
- Let `add-note` and `link` allocate IDs for new notes and edges. Pass `--doc-id` or `--edge-id` only when intentionally updating an existing record; explicit duplicate IDs are treated as update intent for edges and rejected for create-only note/import commands.
- Use `closure` for compact branch or target-family closures that cite evidence and reopen criteria.
- Use `maxtac-core-modeling` for formal entities, relations, invariants, formulas, assumptions, unknowns, and contradictions; use corpus notes for narrative research knowledge and retrieval.

## Anti-Tunnel Retrieval

`orient` intentionally diversifies by facets such as `subsystem`, `boundary`, and `knowledge-kind`. When the orientation pack shows a single dominant area, choose one of:

- deepen with a named checkpoint and proof target;
- pivot to an adjacent underexplored tag;
- consolidate the branch into a note and edge;
- close the branch with a negative-result note;
- export a model or auditor prompt for independent review.

Do not keep writing into the same visible folder because it is nearby. Query the corpus and choose the next write by tags, graph edges, unknowns, and evidence.

## References

Read `references/corpus-taxonomy.md` when choosing facets, note kinds, statuses, edge predicates, or migration behavior. Read `schemas/corpus-record.schema.json` only when exact machine-readable record shape matters.
