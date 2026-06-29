---
name: maxtac-supply-chain-source-artifact-diff
description: "Use this skill when MaxTAC Supply Chains needs source-to-package, source-to-release, source-to-container, build provenance, signature, SLSA, SBOM, or artifact integrity diffing for supply-chain compromise research."
---

# MaxTAC Source Artifact Diff

Use this skill when the security question is whether the shipped artifact matches the intended source and build process. This includes npm packages, PyPI sdists and wheels, crates, gems, jars, NuGet packages, Go modules, release tarballs, installers, browser extensions, containers, actions, model bundles, and binary releases.

## Diff Packet

Store results under `audits/supply-chain/<case-id>/source-artifact-diff.md`:

- Source anchor: repository URL, commit SHA, tag object ID, submodules, generated-code commit, release branch, or source archive.
- Artifact anchor: package coordinates, version, registry URL, digest, image manifest digest, release asset URL, signature, attestation, SBOM, or installer hash.
- Build claim: documented build command, CI workflow, builder identity, SLSA level or provenance predicate, reproducibility claim, signing identity, and expected generated outputs.
- Differences: added files, removed files, generated files, binaries, minified bundles, scripts, native extensions, vendored dependencies, permissions, metadata, and dependency versions.
- Security relevance: executable path, install/build/runtime trigger, credential access, network egress, policy bypass, artifact substitution, or consumer impact.
- Verdict: expected generated output, benign packaging difference, suspicious mismatch, confirmed artifact tampering, or needs reproduction.

## Workflow

1. Preserve immutable identifiers: source commit/tag object, package digest, registry metadata, image digest, signature certificate, attestation subject digest, SBOM digest, and retrieval timestamp.
2. Normalize file lists before diffing. Compare paths, modes, symlinks, shebangs, generated artifacts, archives nested inside archives, and binary metadata.
3. Diff the nearest known-good artifact against the suspicious artifact before diffing source. This separates normal packaging churn from compromise indicators.
4. Diff source tag to artifact. Treat generated files as suspicious until the generator, input, and build command are identified.
5. Verify provenance and signatures. Check whether the attestation subject digest matches the artifact, whether the builder identity is expected, and whether the signature is attached to the exact digest being consumed.
6. Send suspicious code paths to Source or Binary pack for deeper review.
7. Send release-authority questions to `maxtac-supply-chain-cicd-release-takeover`.

## Ecosystem Notes

- npm: inspect `package.json`, lifecycle scripts, packed file list, `files`, `.npmignore`, bundled dependencies, provenance, and tarball integrity.
- PyPI: inspect sdist versus wheel, `setup.py`, `pyproject.toml`, entry points, native extensions, generated files, and `RECORD` hashes.
- Go: inspect module proxy zip, `go.sum`, `replace`, vendoring, generated code, cgo, and tag-to-module path consistency.
- Cargo: inspect crate contents, `build.rs`, proc macros, features, vendored code, and registry checksum.
- Maven/Gradle/NuGet/RubyGems: inspect package metadata, build scripts, plugin hooks, native artifacts, signing, repository priority, and transitive resolution.
- Containers: inspect manifest digest, base image digest, Dockerfile provenance, layer diff, entrypoints, package manager state, and embedded credentials.

## Hard Rules

- Do not trust tag names, branch names, image tags, or package versions as immutable evidence. Record digests and object IDs.
- Do not treat a signature as sufficient if it signs a different digest, an unexpected builder, or a mutable tag.
- Do not mark generated files benign until the generator and inputs are known.
- Do not flatten archives when path context, symlinks, permissions, or nested payloads matter.
