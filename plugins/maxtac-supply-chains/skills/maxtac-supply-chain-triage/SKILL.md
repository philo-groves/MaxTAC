---
name: maxtac-supply-chain-triage
description: "Use this skill when supply-chain research needs dependency, package-manager, build, CI/CD, artifact provenance, signing, container, Kubernetes, registry, or release-pipeline triage."
---

# MaxTAC Supply Chain Triage

Use this skill for dependency and release-path vulnerability research. The goal is to map how source becomes a shipped artifact, what trust assumptions bind each handoff, and where an attacker can influence code, configuration, credentials, packages, images, or metadata.

## Operating Rules

- Start from the artifact or deployment boundary: package, container image, binary release, extension, installer, model, firmware bundle, CI output, or production deployment.
- Preserve provenance evidence as artifacts: lockfiles, SBOMs, package metadata, workflow files, build logs, signatures, attestations, container digests, registry metadata, and release manifests.
- Do not report dependency presence alone as a vulnerability. Tie it to reachability, exploitability, poisoning risk, credential exposure, policy bypass, or release integrity impact.
- Use `maxtac-source` when code review, OpenGrep, or call-graph evidence is needed.
- Use `maxtac-web` when the supply-chain path depends on a web console, webhook, OAuth app, package registry API, or SaaS workflow.

## Triage Workflow

1. Identify the shipped artifact and consumer: package name, image digest, release tag, installer, extension, service, or deployment.
2. Map build inputs: source repositories, submodules, generated code, package managers, lockfiles, base images, toolchains, CI actions, runner images, secrets, and environment variables.
3. Map trust boundaries: maintainer identity, registry namespace, package scope, CI runner isolation, artifact signing, attestation policy, review/approval gates, deploy keys, and cloud IAM permissions.
4. Check attacker influence: dependency confusion, typosquatting, compromised maintainer, mutable tags, cache poisoning, script execution, workflow injection, untrusted PR execution, artifact substitution, and secret exfiltration.
5. Preserve negative evidence: pinned digests, lockfile integrity, hermetic builds, verified signatures, least-privilege runners, protected branches, review gates, and isolated credentials.

## Supply Chain Packet

```markdown
## Supply Chain Triage Packet

- Artifact or release boundary:
- Consumer or deployment target:
- Build inputs:
- Package managers or registries:
- CI/CD entrypoints:
- Secrets and credentials involved:
- Signing or attestation model:
- Container or runtime boundary:
- Security invariant:
- Attacker-controlled input:
- Suspect dependency, workflow, or provenance gap:
- Evidence collected:
- Evidence still needed:
- Suggested tools: Source/SAST / Web / Auditors
- Suggested auditor filters:
- Candidate hypothesis:
- Confidence: low / medium / high
```

## Auditor Routing

Use the Supply Chains pack's auditor MCP tools when available. Good starting filters include `supply-chain`, `cicd`, `package-manager`, `dependency-confusion`, `container`, `kubernetes`, `cloud`, `iam`, `secrets`, `registry`, `lockfile`, `signature`, and `attestation`.
