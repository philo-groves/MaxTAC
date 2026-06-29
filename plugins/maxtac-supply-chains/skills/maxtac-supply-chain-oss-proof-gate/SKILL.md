---
name: maxtac-supply-chain-oss-proof-gate
description: "Use this skill when MaxTAC Supply Chains needs OSS, dependency, package, or supply-chain finding proof gating before reporting, including Google Bug Hunters OSS-style scope, dependency-owner, and real-world impact checks."
---

# MaxTAC OSS Proof Gate

Use this skill before reporting OSS, dependency, package, registry, CI/CD, or supply-chain findings. It converts a promising hypothesis into a scope and proof decision: reportable, needs product impact, third-party first, duplicate or known issue, not a security issue, or still needs evidence.

This skill is inspired by modern OSS VRP gating, including Google Bug Hunters' OSS rules and 2026 emphasis on filtering low-quality reports for real-world impact. Always read the current program rules for the target before making a final scope claim.

## Helper

Use `python3 <skill-dir>/scripts/oss_gate.py` to create and lint a gate packet:

```bash
python3 <skill-dir>/scripts/oss_gate.py create \
  --output audits/supply-chain/<case-id>/oss-proof-gate.md \
  --case-id <case-id> \
  --target "package or project" \
  --ecosystem npm \
  --claim "dependency confusion reaches release CI"

python3 <skill-dir>/scripts/oss_gate.py lint audits/supply-chain/<case-id>/oss-proof-gate.md
```

Run `lint --strict` after filling the packet.

## Gate Packet

Every packet must answer:

- Program and scope basis: in-scope project, package, organization, repository, product, dependency relationship, or public OSS program rule.
- Target ownership: first-party project, third-party dependency, transitive dependency, abandoned namespace, fork, mirror, vendored code, generated code, or container base image.
- Affected consumer: who installs, builds, imports, deploys, signs, or serves the compromised artifact.
- Attacker control: package publish, maintainer account, registry namespace, artifact upload, CI event, workflow input, cache, OIDC claim, source change, or dependency resolution.
- Security impact: code execution, credential theft, release artifact poisoning, signing abuse, production deploy, data access, account takeover, or material integrity loss.
- Proof quality: static proof, package diff, provenance mismatch, controlled PoV, isolated dynamic run, affected-product reproduction, negative control, and evidence hashes.
- Exclusions checked: dependency presence only, stale CVE only, speculative malware, local-only developer misconfiguration, unsupported version, test/demo path, no affected consumer, or no realistic attacker path.
- Decision: reportable, needs product-impact proof, third-party dependency owner first, not actionable, duplicate or known issue, or needs review.

## Google-Style OSS Gating

When a target follows a Google Bug Hunters OSS-style policy, apply these checks before report drafting:

- Verify the project or package is public OSS and within the named program scope. Do not assume every dependency of an in-scope project is itself in scope.
- For third-party dependencies, determine whether the program expects notification or fixing upstream before submitting downstream impact. Preserve upstream issue/advisory links and dates.
- Prove real-world impact on the in-scope consumer, not only theoretical breakage in the dependency.
- Prefer exploit or compromise proof that crosses a supported trust boundary: package installation, CI build, release artifact, production runtime, credential boundary, or user data boundary.
- De-escalate pure scanner output, dependency presence, unsupported versions, best-practice gaps, or known duplicate advisories unless the target-specific impact is new.

## Reportability Ladder

- `reportable`: in-scope ownership or dependency relationship, reachable attacker control, supported consumer impact, positive proof, and negative control are present.
- `needs_product_impact`: dependency or package issue is plausible, but impact on the program's project or shipped artifact is not proven.
- `third_party_first`: issue appears to belong to an upstream dependency or registry owner and program rules require upstream handling first.
- `needs_review`: scope or proof is ambiguous.
- `not_actionable`: no security boundary, no affected consumer, unsupported target, theoretical-only claim, duplicate known issue, or maintenance bug.

## Hard Rules

- Do not report dependency presence, CVE existence, or a public advisory as a new supply-chain finding without new in-scope impact.
- Do not claim compromise from suspicious indicators alone. Tie indicators to attacker control and affected consumer impact.
- Do not skip program-specific policy. Google, open-source foundations, package registries, and vendor VRPs gate third-party dependency issues differently.
- Do not include malicious payloads, secrets, or personal data directly in the report body. Reference sanitized evidence artifacts.
