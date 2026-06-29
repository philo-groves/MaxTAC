---
name: maxtac-supply-chain-triage
description: "Use this skill when supply-chain research needs initial routing across dependency, package-manager, build, CI/CD, artifact provenance, signing, registry, container artifact, release-pipeline, compromise-hunting, or OSS proof-gating workflows."
---

# MaxTAC Supply Chain Triage

Use this skill as the entrypoint for dependency and release-path vulnerability research. The goal is to map how source becomes a shipped artifact, what trust assumptions bind each handoff, and which focused Supply Chains skill should own the next pass.

## Operating Rules

- Start from the artifact or deployment boundary: package, container image, binary release, extension, installer, model, firmware bundle, CI output, or production deployment.
- Preserve provenance evidence as artifacts: lockfiles, SBOMs, package metadata, workflow files, build logs, signatures, attestations, container digests, registry metadata, and release manifests.
- Do not report dependency presence alone as a vulnerability. Tie it to reachability, exploitability, poisoning risk, credential exposure, policy bypass, or release integrity impact.
- Use `maxtac-source` when code review, OpenGrep, or call-graph evidence is needed.
- Use `maxtac-web` when the supply-chain path depends on a web console, webhook, OAuth app, package registry API, or SaaS workflow.
- Use `maxtac-cloud` when the surviving path depends on cloud IAM, workload identity, managed Kubernetes identity, runtime metadata, cloud storage, or cloud deployment authority.

## Skill Routing

- Use `maxtac-supply-chain-compromise-hunt` when the question is "was this package, release, dependency, container, maintainer account, or build path compromised?"
- Use `maxtac-supply-chain-source-artifact-diff` when a shipped package, image, installer, binary, wheel, jar, gem, crate, or release asset must be compared against source and provenance.
- Use `maxtac-supply-chain-cicd-release-takeover` when untrusted code, workflow configuration, caches, artifacts, OIDC, runners, or CI tokens may reach publishing or deployment authority. Hand off to Cloud when the proof depends on AWS/Azure/GCP permissions after the CI/CD boundary is crossed.
- Use `maxtac-supply-chain-oss-proof-gate` before reporting OSS or dependency findings, especially when the target program requires real product impact, dependency-owner notification, or proof that a compromise path affects an in-scope consumer.

## Triage Workflow

1. Identify the shipped artifact and consumer: package name, image digest, release tag, installer, extension, service, or deployment.
2. Map build inputs: source repositories, submodules, generated code, package managers, lockfiles, base images, toolchains, CI actions, runner images, secrets, and environment variables.
3. Map trust boundaries: maintainer identity, registry namespace, package scope, CI runner isolation, artifact signing, attestation policy, review/approval gates, deploy keys, and cloud IAM permissions.
4. Check attacker influence: dependency confusion, typosquatting, compromised maintainer, mutable tags, cache poisoning, script execution, workflow injection, untrusted PR execution, artifact substitution, credential exfiltration, and release signing abuse.
5. Preserve negative evidence: pinned digests, lockfile integrity, hermetic builds, verified signatures, least-privilege runners, protected branches, review gates, isolated credentials, dependency-source mapping, and provenance enforcement.
6. Route to the focused skill that best matches the surviving hypothesis.

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
- Suggested tools: Source/SAST / Web / Cloud / Auditors
- Suggested auditor filters:
- Candidate hypothesis:
- Recommended next skill:
- Confidence: low / medium / high
```

## Auditor Routing

Use the Supply Chains pack's auditor MCP tools when available. Good starting filters include `supply-chain`, `cicd`, `package-manager`, `dependency-confusion`, `container`, `registry`, `lockfile`, `signature`, `attestation`, `provenance`, `release`, and `oss`. Use Cloud auditor filters for cloud IAM, managed Kubernetes, runtime metadata, or cloud data-plane questions.
