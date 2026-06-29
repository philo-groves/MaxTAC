# MaxTAC for Supply Chains

MaxTAC for Supply Chains adds package compromise hunting, source-to-artifact diffing, artifact capture helpers, CI/CD release-takeover analysis, OSS proof gating, dependency and registry triage, provenance, signing, container artifact, and release-pipeline workflows.

Use this pack with MaxTAC Core when the research question involves how source, dependencies, workflows, credentials, packages, images, or build artifacts become trusted releases or deployments.

## When To Use

- Suspected package, release, maintainer, registry, container, or build-path compromise.
- Source-to-package, source-to-release, source-to-container, signature, attestation, SBOM, or artifact integrity checks.
- CI/CD workflow, runner, cache, OIDC, artifact promotion, signing, publishing, or deployment takeover analysis.
- OSS or dependency finding proof gating before reporting.
- Dependency confusion, typosquatting, lockfile drift, private registry fallback, package scripts, and transitive trust flaws.

## Skills

- `maxtac-supply-chain-triage`: initial routing across dependency, build, registry, container, provenance, compromise, and proof-gating workflows.
- `maxtac-supply-chain-compromise-hunt`: SOTA compromise hunting for suspicious packages, dependencies, releases, containers, registry events, and maintainer activity.
- `maxtac-supply-chain-source-artifact-diff`: source-to-artifact integrity, provenance, signature, SLSA, SBOM, package, and image diffing.
- `maxtac-supply-chain-cicd-release-takeover`: untrusted CI input to trusted release, signing, publishing, or deployment authority.
- `maxtac-supply-chain-oss-proof-gate`: OSS, dependency, package, and supply-chain reportability gating with impact checks.

## Typical Pairings

- Supply Chains + Source when reachability depends on source code.
- Supply Chains + Web when registry APIs, OAuth apps, SaaS consoles, or webhook flows matter.
- Supply Chains + Cloud when CI/CD OIDC, cloud deployment roles, managed Kubernetes identities, registries, or cloud runtime trust paths matter.
- Supply Chains + Binary when installers, native packages, release binaries, or containers need binary inspection.
- Supply Chains + program packs when Android, Apple, or Microsoft proof rules govern the shipped artifact.

## Output Artifacts

Supply-chain workflows commonly produce:

- `proof/supply-chain/<case-id>/` evidence freezes and source-artifact diffs.
- `tmp/supply-chain/<case-id>/` working packets for compromise hunts, CI/CD takeover analysis, and OSS proof gates.
- Package metadata, lockfiles, registry responses, SBOMs, signatures, attestations, image digests, release asset hashes, and workflow logs.
- Evidence freeze manifests created with `package-freeze.py`.
- Directory or archive diff packets created with `artifact-diff.py`.
- Proof-gate packets created with `oss_gate.py`.

## Boundary

Do not report dependency presence, scanner output, suspicious indicators, or public advisories as new findings without affected-consumer impact and proof. Use Source, Binary, Web, or Cloud when the next step needs code reachability, reverse engineering, web workflow evidence, or cloud identity/runtime proof.
