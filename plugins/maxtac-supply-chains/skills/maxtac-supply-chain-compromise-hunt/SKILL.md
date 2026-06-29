---
name: maxtac-supply-chain-compromise-hunt
description: "Use this skill when MaxTAC Supply Chains needs SOTA compromise hunting for suspicious packages, dependencies, release assets, containers, maintainer accounts, registry events, build tools, or artifact provenance anomalies."
---

# MaxTAC Supply Chain Compromise Hunt

Use this skill to hunt for actual or likely supply-chain compromise, not ordinary vulnerable-dependency triage. Start from a suspicious artifact, package, version, release, registry event, maintainer action, dependency update, CI artifact, or deployed image, then build a falsifiable compromise hypothesis.

## Hunt Packet

Store working findings under `tmp/supply-chain/<case-id>/compromise-hunt.md`:

- Artifact: package, version, image digest, release asset, commit, tag, lockfile entry, action, build tool, installer, or registry event.
- Ecosystem: npm, PyPI, Go, Cargo, Maven, Gradle, NuGet, RubyGems, Packagist, Homebrew, apt/yum, container registry, GitHub Actions, or other.
- Consumer boundary: developer workstation, CI, build farm, package publish step, production runtime, installer, extension host, or cloud deployment.
- Compromise hypothesis: maintainer/account takeover, token leak, malicious maintainer release, typosquat, dependency confusion, artifact substitution, CI cache poisoning, compromised action, binary/toolchain swap, container base-image compromise, or staged malware.
- Trigger conditions: install, import, test, build, postinstall, publish, runtime, platform-specific, environment-variable gated, CI-only, time-delayed, or command-line gated.
- Positive evidence, counterevidence, and remaining proof gaps.
- Impact path: code execution, credential theft, source theft, artifact poisoning, deployment takeover, signing abuse, data exfiltration, persistence, or lateral movement.

## Evidence Freeze Helper

Use `package-freeze.py` when a case needs a durable manifest of package metadata, release assets, lockfiles, SBOMs, signatures, attestations, registry responses, or hashes:

```text
python plugins/maxtac-supply-chains/skills/maxtac-supply-chain-compromise-hunt/scripts/package-freeze.py create --case-id <case-id> --target "<package-or-release>" --ecosystem <ecosystem> --coordinates <name> --version <version> --artifact-url <url>
python plugins/maxtac-supply-chains/skills/maxtac-supply-chain-compromise-hunt/scripts/package-freeze.py add-artifact --manifest proof/supply-chain/<case-id>/freeze/manifest.json --path <local-artifact> --category package
python plugins/maxtac-supply-chains/skills/maxtac-supply-chain-compromise-hunt/scripts/package-freeze.py lint --manifest proof/supply-chain/<case-id>/freeze/manifest.json
```

Store the manifest with the hunt packet and cite its SHA-256 values in reports.

## High-Signal Leads

Prioritize leads with multiple independent signals:

- Metadata drift: new publisher, maintainer churn, unusual publish time, fresh account, MFA or provenance change, yanked/replaced version, registry namespace transfer, unexpected tag movement, or release asset replaced after tag.
- Source/package mismatch: files in the published artifact not present in the tagged source, generated files that cannot be reproduced, hidden dotfiles, binary blobs, minified bundles, packed archives, new obfuscation, or changed install hooks.
- Behavior drift: new process execution, network egress, credential/environment reads, filesystem traversal, shell evaluation, native binary loading, dynamic import, reflective eval, or platform-specific payload selection.
- Dependency graph drift: new transitive dependency with install scripts, unexpected registry fallback, loose version range pulling a malicious release, lockfile integrity mismatch, or stale internal package name.
- CI/release drift: action pinned to mutable tag, cache restore from untrusted branch, `pull_request_target` or `workflow_run` privilege boundary, artifact promoted from untrusted job, new OIDC subject, or publish token exposed to untrusted code.
- External corroboration: ecosystem advisory, maintainer warning, registry takedown, malware signature, public incident timeline, suspicious domains, or matching IoCs.

## Analysis Workflow

1. Freeze evidence. Record URLs, package metadata JSON, release asset hashes, tag object IDs, image digests, lockfiles, workflow files, SBOMs, signatures, attestations, and timestamps before running anything. Use `package-freeze.py` when a local manifest improves reproducibility.
2. Diff the suspicious version against the nearest known-good version and against the claimed source tag. Use `maxtac-supply-chain-source-artifact-diff` when source-to-artifact integrity matters.
3. Classify execution surfaces: install scripts, build scripts, test hooks, import-time code, native extensions, container entrypoints, CI actions, GitHub composite steps, Dockerfile layers, release scripts, and runtime plugins.
4. Trace data access: environment variables, credential files, npm/PyPI/GitHub/GCP/AWS/Azure tokens, SSH keys, package manager config, cloud metadata, source tree, home directory, and CI workspace.
5. Bound blast radius by consumer. A malicious package version is not the same as compromise of the target program unless an in-scope consumer installs, builds, imports, deploys, or republishes it.
6. Run `maxtac-supply-chain-oss-proof-gate` before final reporting.

## Safe Handling

- Prefer static analysis, archive extraction, and inert sandboxes. Do not run suspicious code on a developer workstation or with real credentials.
- If dynamic behavior is required, use an isolated throwaway environment with egress controls, fake secrets, recorded DNS/HTTP, snapshots, and no mounted sensitive directories.
- Do not contact suspected attacker infrastructure unless the research plan explicitly allows controlled network observation.
- Preserve malicious artifacts as evidence but avoid redistributing payloads in final reports unless the program asks for them.

## Hard Rules

- Do not call a package compromised solely because it is vulnerable, unpopular, obfuscated, or has a new maintainer.
- Do not report a global ecosystem compromise when evidence only proves local project misconfiguration.
- Do not treat IoCs as proof without an affected consumer path.
- Do not execute install hooks, build scripts, or containers with real tokens.
