---
name: maxtac-supply-chain-cicd-release-takeover
description: "Use this skill when MaxTAC Supply Chains needs advanced CI/CD, workflow, runner, cache, OIDC, release, publishing, signing, artifact promotion, or deployment takeover analysis."
---

# MaxTAC CI/CD Release Takeover

Use this skill when untrusted input may reach trusted build, publish, signing, deployment, or release authority. The central question is whether an attacker can move from a low-trust event to a high-trust artifact or credential.

## Takeover Packet

Store results under `audits/supply-chain/<case-id>/cicd-release-takeover.md`:

- Low-trust source: fork PR, issue comment, branch, tag, scheduled workflow, dependency update, registry package, cache key, artifact upload, external webhook, or self-hosted runner job.
- Trust boundary: workflow trigger, job dependency, artifact promotion, environment approval, OIDC federation, secret exposure, runner isolation, signing, package publish, or deployment.
- High-trust authority: repo write token, release upload, package publish token, signing key, cloud deploy role, production credentials, artifact registry, container push, or app-store/notarization path.
- Exploit sequence: exact event, controlled file or parameter, privileged step reached, token or artifact gained, and resulting release-path impact.
- Controls and counterevidence: branch protection, required review, environment approval, token permissions, pinned actions, digest pinning, artifact verification, cache scoping, runner isolation, and OIDC subject constraints.

## High-Risk Patterns

- `pull_request_target`, `workflow_run`, `issue_comment`, or reusable workflows that checkout or execute attacker-controlled code with elevated token permissions.
- Mutable action refs, unpinned Docker actions, compromised third-party actions, broad `GITHUB_TOKEN` permissions, or secrets passed to untrusted jobs.
- Artifact handoff where an untrusted job uploads a build output, test report, binary, coverage file, or metadata consumed by a trusted deploy, release, or signing job.
- Cache poisoning where untrusted input controls keys, paths, restore prefixes, compiler caches, dependency caches, or generated tool outputs used by trusted builds.
- OIDC federation where subject, audience, environment, branch, workflow, or repository constraints allow untrusted events to assume cloud or publish roles.
- Self-hosted runners exposed to forks, shared across trust zones, retaining workspace state, mounting Docker socket, or holding long-lived credentials.
- Release scripts that publish from local developer machines, mutable tags, branch names, unverified artifacts, or unauthenticated release assets.

## Workflow

1. Draw the event-to-authority graph. Include triggers, jobs, dependencies, artifacts, caches, environments, tokens, runner labels, and external services.
2. Identify the first attacker-controlled byte and the first privileged action that consumes it.
3. Prove token and artifact boundaries separately. A workflow injection is not a release takeover unless it can reach a high-trust token, artifact, or deployment decision.
4. Check default and explicit permissions. Record `permissions`, environment secrets, `secrets: inherit`, OIDC claims, branch filters, path filters, and approval gates.
5. Test negative controls where possible: safe branch, fork context, removed artifact, narrowed permission, digest-pinned action, or blocked environment approval.
6. Use `maxtac-supply-chain-oss-proof-gate` before reporting program-scoped OSS or dependency findings.

## Hard Rules

- Do not claim secret exfiltration from a workflow unless a secret is actually exposed to the attacker's job or reachable through a downstream trusted job.
- Do not claim release takeover from code execution in CI alone. Tie it to publish, signing, artifact promotion, deployment, or credential authority.
- Do not ignore `permissions: read-all` or environment approvals that break the chain.
- Do not run destructive workflow tests against live release infrastructure.
