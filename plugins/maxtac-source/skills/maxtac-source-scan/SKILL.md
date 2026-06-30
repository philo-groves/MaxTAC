---
name: maxtac-source-scan
description: "Use this skill when MaxTAC Source needs a Git-backed diff scan, repository or scoped-path source review, deterministic source worklists, thin exact-path closure, coverage receipts, closure validation, or canonical MaxTAC result-contract output for source security review."
---

# MaxTAC Source Scan

Use this skill for bounded source-code security review where coverage claims must be auditable. It is heavier than `maxtac-sast-surface-triage`: surface triage creates hypotheses, while Source Scan creates a worklist, closes every reviewed surface with receipts, and feeds `maxtac-core-contracts`.

Use thin closure for tiny exact scopes, such as a one-file helper or a narrow generated source family, when the durable conclusion is compact and no reportable chain survived. Thin closure keeps a source receipt without expanding the target into a full packet/report train.

## Scan Artifacts

By default, source scans live under the MaxTAC workspace:

```text
contracts/source-scans/<scan-id>/
  metadata.json
  worklist.jsonl
  coverage.jsonl
  receipts/
```

The matching canonical result bundle should live under:

```text
contracts/<scan-id>/result.json
```

## Workflow

1. Initialize a worklist for the exact scope.
   - Use `mode diff` for PRs, commits, branch diffs, and working-tree changes.
   - Use `mode repo` for whole repositories.
   - Use `mode scoped` for selected directories or packages.
2. Create a matching Core result contract with `maxtac-core-contracts`.
3. Review every row in `worklist.jsonl`.
   - Use `maxtac-source-codebase-memory`, `maxtac-sast-surface-triage`, `maxtac-sast-control-flow-graph`, `maxtac-sast-opengrep`, and domain auditors as needed.
   - Add supporting files only when they are needed to understand a row's security behavior.
4. For each row, write a receipt with `receipt`.
5. Add reportable findings and reviewed surfaces to the Core result contract.
6. Run `validate` on the source scan and `validate` on the Core result contract before final reporting.
7. Run Core `finalize` to project the deterministic report.

## Thin Closure Workflow

Use this path when all are true:

- the scope is exact and small, usually one to three files or one helper family;
- the conclusion is negative, rejected, not applicable, deferred, or needs follow-up, not reportable;
- the key proof is caller/reachability/privilege evidence plus source inspection;
- no new formal model or multi-artifact narrative packet is needed.

Create the source receipt in one step:

```text
python3 <skill-dir>/scripts/source_scan.py thin-close \
  --root <workspace-root> \
  --target-path <repo> \
  --scan-id wordexp-helper \
  --path lib/libc/gen/wordexp-helper.c \
  --risk-area privileged-caller-reachability \
  --disposition no_issue_found \
  --note "Helper is simple; libc wordexp shells through it; no privileged caller found." \
  --evidence research/artifacts/system-cmds/wordexp-helper/caller-proof.md
```

Then create a Core thin result bundle with `maxtac-core-contracts thin-closure`, update or milestone any existing ledger candidate, and write one corpus `closure` note. Do not create separate surface packets, OpenGrep mini-reports, model entities, and expanded narrative reports unless the target stops being tiny or the conclusion becomes reportable.

## Commands

Initialize a diff scan:

```text
python3 <skill-dir>/scripts/source_scan.py init --root <workspace-root> --target-path <repo> --mode diff --base <base> --head <head> --scan-id <id>
```

Initialize a working-tree scan:

```text
python3 <skill-dir>/scripts/source_scan.py init --root <workspace-root> --target-path <repo> --mode working-tree --scan-id <id>
```

Initialize a repo or scoped scan:

```text
python3 <skill-dir>/scripts/source_scan.py init --root <workspace-root> --target-path <repo> --mode scoped --scope src --scope packages/auth --scan-id <id>
```

Close a row:

```text
python3 <skill-dir>/scripts/source_scan.py receipt --scan-dir <workspace-root>/contracts/source-scans/<id> --path src/export.py --disposition no_issue_found --risk-area authz --note "Route guard dominates export helper."
```

Record a reportable finding row:

```text
python3 <skill-dir>/scripts/source_scan.py receipt --scan-dir <scan-dir> --path src/export.py --disposition reported --risk-area authz --finding-id finding-0001 --note "Missing tenant check survives validation."
```

Check closure:

```text
python3 <skill-dir>/scripts/source_scan.py status --scan-dir <scan-dir>
python3 <skill-dir>/scripts/source_scan.py validate --scan-dir <scan-dir>
```

## Dispositions

- `reported`: became a canonical finding.
- `no_issue_found`: reviewed and no credible issue survived.
- `rejected`: plausible candidate was ruled out with counterevidence.
- `not_applicable`: row does not exercise the risk class or product boundary.
- `needs_follow_up`: real proof gap remains.
- `deferred`: intentionally left open with a concrete reason.

## Hard Rules

- Do not claim source scan coverage until `source_scan.py validate` succeeds, or explicitly state the rows left as `needs_follow_up` or `deferred`.
- Do not close a row because a neighboring row has a cleaner finding. Close the exact row with evidence or defer it.
- Do not broaden a diff scan into a repo-wide scan unless the user asks. Supporting files are context, not new scope.
- Do not turn source-scan rows into durable research-library facts until they are validated or rewritten as stable negative knowledge.
- Do not author final reports directly when a Core result contract exists. Update the contract and regenerate the report.
- Do not use thin closure for reportable findings, multi-step chains, privileged reachable behavior, contested conclusions, or targets whose reusable architecture needs a model.
