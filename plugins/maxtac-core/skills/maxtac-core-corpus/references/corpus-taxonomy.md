# Corpus Taxonomy

Use this reference when choosing note kinds, statuses, tags, and graph predicates for the MaxTAC research corpus.

## Note Kinds

- `architecture`: durable system structure, components, identity sources, control flow, data flow, trust boundaries, state machines, or ownership.
- `invariant`: narrative explanation of a security rule. Put formal invariant IDs in `maxtac-core-modeling`.
- `negative-result`: confirmed non-issue, blocked path, dominant guard, unreachable route, or disproven assumption.
- `open-question`: missing fact that can change the security conclusion.
- `proof-note`: proof setup, proof preconditions, replay constraints, or proof interpretation.
- `hypothesis`: bounded candidate path that is not yet a finding.
- `triage-summary`: compact triage result that routes future audit/tool work.
- `model-summary`: prose explanation of a `models/<model-id>/` security model.
- `closure`: compact branch, target-family, or thin-review closure with conclusion, evidence, and reopen criteria.
- `decision`: branch closure, scoping decision, de-escalation rationale, or accepted limitation.
- `handoff`: what the next session or subagent should read and do.
- `reference`: external docs, background notes, imported research, or supporting context.

## Document Status

- `draft`: useful but incomplete, under-tagged, or not yet evidence-backed.
- `candidate`: plausible and worth retaining, but not yet directly observed.
- `observed`: seen in code, runtime evidence, artifacts, docs, or an audit.
- `confirmed`: stable enough for future sessions to rely on.
- `negative`: stable negative knowledge.
- `stale`: superseded by version, architecture, scope, or stronger evidence.
- `superseded`: replaced by another note.
- `artifact-only`: retained for provenance but not durable prose.

Use evidence for `observed`, `confirmed`, `negative`, `stale`, `superseded`, and `artifact-only`.

## Core Facets

Use `facet=value` tags. Prefer lowercase hyphenated values.

- `domain`: `source`, `web`, `cloud`, `binary`, `supply-chain`, `android`, `apple`, `microsoft`, `core`.
- `subsystem`: stable component or product area, such as `export-api`, `identity-broker`, `kernel-vfs`, `release-pipeline`.
- `boundary`: `tenant`, `sandbox`, `iam`, `process`, `origin`, `signing`, `parser`, `filesystem`, `kernel-user`, `broker-client`.
- `asset`: protected asset such as `tenant-data`, `signing-key`, `kernel-memory`, `release-authority`, `billing-state`, `privacy-data`.
- `actor`: caller or principal class such as `anonymous-user`, `tenant-member`, `tenant-admin`, `support-user`, `sandboxed-renderer`, `ci-runner`.
- `knowledge-kind`: `architecture`, `invariant`, `negative`, `question`, `proof`, `closure`, `decision`, `handoff`, `hypothesis`.
- `phase`: `prepare`, `scan`, `validation`, `primitive-proof`, `chain-proof`, `reporting`.

Additional useful facets:

- `version`: product, build, branch, package, firmware, or API version.
- `language`: implementation language or decompiler view.
- `tool`: evidence-producing tool, when the note summarizes tool output.
- `model`: related `maxtac-core-modeling` model ID.
- `finding`: related primitive or chain ID.

## Edge Predicates

Use graph edges for relationship structure. Prefer these predicates:

- `refines`: newer note narrows or improves the older note.
- `supersedes`: newer note replaces the older note.
- `contradicts`: two notes cannot both be true without resolution.
- `supports`: one note provides evidence or context for another.
- `depends_on`: a note depends on another fact, assumption, or open question.
- `derived_from`: a note was synthesized from an artifact or previous note.
- `mentions_invariant`: a note references a formal invariant or invariant note.
- `closes_unknown`: a note answers an open question.
- `opens_question`: a note introduces follow-up uncertainty.
- `shares_boundary_with`: two notes touch the same security boundary.
- `handoff_to`: a note routes work to another target, skill, auditor, or phase.

Use `observed` or `confirmed` edges only with evidence.

## Migration Rules

When importing old `research/**/*.md`:

1. Keep the original markdown as evidence unless it was already raw output.
2. Create one compact canonical note per stable idea, not one note per old file if the file mixes several topics.
3. Tag by facets before writing the note.
4. Link imported notes with `derived_from`, `refines`, `supersedes`, or `contradicts` when relationships are clear.
5. Move obsolete raw markdown under `research/artifacts/imported-markdown/` only after the canonical note preserves the durable knowledge.

## Generated Views

Files under `research/views/` are generated and may be overwritten:

- `index.md`: recent notes and by-kind grouping.
- `facets.md`: tag counts by facet.
- `open-questions.md`: open questions and negative knowledge.
- `graph.mmd`: Mermaid graph of corpus note edges.

Do not manually maintain a hierarchy in generated views. If a view is wrong, update note metadata, tags, or edges, then rerun `compile-views`.
