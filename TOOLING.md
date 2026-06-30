## MaxTAC Tooling Inventory

Install only the tools needed by the active plugin packs and current target. Core needs Python for helper scripts; domain packs route to target-specific tools.

## Core

| Tool | Used for |
| --- | --- |
| Python | Workspace helpers, ledger helpers, evidence scripts, and the SQLite auditor registry. |
| Core corpus helper | Faceted research notes, tags, graph edges, generated corpus views, import, search, lint, and anti-tunnel orientation packs. |
| Core model helper | Security model JSON, invariant dictionaries, invariant receipts, model projections, model-backed auditor prompts, and workspace model search. |
| Core contracts thin closure | Compact non-reportable closure bundles with coverage receipts, proof evidence, and reopen criteria for tiny exact scopes. |
| Core false-negative review | Negative-evidence score, explicit gap register, primitive graveyard prompts, caller expansion, patch-diff, chain-composer, and invariant-receipt reopen actions. |
| Codex subagents and goals | Auditor prompts, registry-backed auditor lookup, verifier debates, and workflow orchestration. |

## Source

| Tool | Used for | Pack |
| --- | --- | --- |
| ripgrep (`rg`) | Fast source search during surface triage and path collection. | Source |
| Git | Diff, branch, commit, and repository worklist generation for Source Scan. | Source |
| codebase-memory-mcp | Optional local MCP/CLI code graph for repository indexing, architecture summaries, structural search, call-path tracing, ADR lookup, and diff impact mapping. | Source |
| OpenGrep (`opengrep`) | Rule authoring, pattern matching, taint-style source-to-sink checks, result packets. | Source |
| Compiler, AST, language-server, static-analysis, code-index, or route-map tools | CFG/call-graph facts, guard dominance, route maps, reachability evidence. | Source |
| DOT or Mermaid-compatible graph output | Persisted control-flow, call-graph, state-machine, or ownership evidence. | Source |
| SARIF, JSON scanner exports, advisory or ticket exports | External finding intake and backlog triage normalization. | Source |
| GitHub CLI or authorized connector export | Optional retrieval of code scanning, Dependabot, advisory, or private report content before local intake normalization. | Source |

## Binary

| Tool | Used for | Pack |
| --- | --- | --- |
| Ghidra, `analyzeHeadless`, Java, PyGhidra | Headless import, decompilation, p-code, scripting, type recovery, BSim, version tracking, emulation. | Binary |
| radare2 suite: `r2`, `rabin2`, `rahash2`, `rafind2`, `radiff2`, `rax2`, `rasm2`, `ragg2`, `r2pipe` | Binary triage, imports, symbols, hashes, search, diffing, ESIL, debugging, scripting, utilities. | Binary |
| LLDB | macOS and native C/C++/LLVM crash replay and debugging. | Binary |
| GDB | Linux and portable ELF crash replay/debugging. | Binary |
| x64dbg | Windows user-mode binary debugging. | Binary |
| WinDbg | Windows kernel-mode, crash dump, and deep OS-component debugging. | Binary |
| Frida | Runtime instrumentation, hooks, and API tracing. | Binary |
| AFL++, libFuzzer, FuzzTest, LibAFL, WinAFL, Honggfuzz | Native parser, binary-only, kernel, protocol, and systems fuzzing. | Binary |
| cargo-fuzz, Go fuzzing, Jazzer, Atheris | Managed-runtime or native-extension fuzzing. | Binary |
| syzkaller, boofuzz, Fuzzilli, Domato | Kernels, syscalls, drivers, custom protocols, and browser engines. | Binary |
| libprotobuf-mutator, Nautilus, Grammarinator, Radamsa | Structured formats, protobuf-like data, grammars, seed expansion. | Binary |

## Web

| Tool | Used for | Pack |
| --- | --- | --- |
| RESTler, Schemathesis | Stateful REST/OpenAPI or schema-backed API fuzzing. | Web |
| Nuclei, Burp Intruder, ZAP Fuzzer, ffuf | Captured HTTP traffic, templates, parameter fuzzing, and manual request fuzzing. | Web |
| WebDriver BiDi | Browser debugging and automation with bidirectional events. | Web |
| Chrome DevTools Protocol (CDP) | Chromium-family browser instrumentation and evidence capture. | Web |
| WebKit debugging tools | Safari, WebKit, WKWebView, WebKitGTK, and WPE inspection. | Web |

## Supply Chains

| Tool family | Used for | Pack |
| --- | --- | --- |
| Package-manager native tools (`npm`, `pnpm`, `yarn`, `pip`, `uv`, `poetry`, `go`, `cargo`, `mvn`, `gradle`, `nuget`, `gem`) | Lockfile, dependency, script, registry, package metadata, packed artifact, and provenance inspection. | Supply Chains |
| SBOM, advisory, and malware scanners (`syft`, `grype`, `osv-scanner`, ecosystem audit tools) | Dependency inventory, advisory context, reachability support, compromise leads, and report artifacts. | Supply Chains |
| CI/CD CLIs and logs (`gh`, runner logs) | Workflow, runner, secret, approval, OIDC, cache, artifact handoff, release, and deployment evidence. | Supply Chains |
| Signing and attestation tools (`cosign`, `slsa-verifier`, `gitsign`, ecosystem provenance tools) | Release integrity, signature, builder identity, SLSA/provenance, and policy evidence. | Supply Chains |
| Container and registry tools (`docker`, `podman`, `skopeo`, `crane`, `oras`) | Image digest, layer diff, build context, base image, registry metadata, and artifact integrity evidence. | Supply Chains |

## Cloud

| Tool | Used for | Pack |
| --- | --- | --- |
| AWS CLI (`aws`) | IAM, STS, S3, KMS, CloudTrail, Access Analyzer, Config, EKS, Lambda, ECS, EC2, and resource evidence. | Cloud |
| Azure CLI (`az`) and Microsoft Graph tooling | Tenant, subscription, RBAC, Entra app, service principal, managed identity, Key Vault, Storage, AKS, Activity Log, and resource evidence. | Cloud |
| Google Cloud CLI (`gcloud`, `gsutil`, `bq`) | Project, folder, IAM, service account, Cloud Storage, BigQuery, KMS, GKE, Cloud Run, audit log, and organization-policy evidence. | Cloud |
| JSON/YAML helpers (`jq`, `yq`) | Policy, audit log, IaC, and CLI transcript normalization. | Cloud |
| Cloud inventory and posture tools (`steampipe`, `prowler`, `ScoutSuite`) | Optional inventory, policy context, and lead generation before manual proof. | Cloud |
| Kubernetes tools (`kubectl`, `helm`) | EKS, AKS, GKE workload identity, RBAC, token, namespace, admission, and pod evidence. | Cloud |
| IaC and policy tools (`terraform`, `terragrunt`, `opa`, `conftest`) | Cloud resource intent, policy-as-code, deployment authority, and drift analysis. | Cloud |

## Android

| Tool | Used for | Pack |
| --- | --- | --- |
| JADX, `jadx-gui`, Java | APK/DEX/JAR/AAR/AAB decompilation, Android resources, mappings, GUI search, smali debugging, JSON/API export. | Android |
| Android Debug Bridge (`adb`) | Device discovery, package metadata, component launch, content-provider probes, logcat, screenshots, recordings, and bugreports. | Android |
| JDWP tools such as `jdb` | Debuggable-app inspection and authorized Java runtime debugging. | Android |
| Frida and frida-tools | Android Java/native hooks, runtime observation, API tracing, and script-backed evidence. | Android |
| Android SDK command-line tools such as `apksigner` and `apkanalyzer` | Signing, certificate, manifest, APK, resource, and package metadata support when available. | Android |

## Program Packs

| Tool | Used for | Pack |
| --- | --- | --- |
| `ipsw` | IPSW/OTA provenance, targeted extraction, kernelcache and dyld artifacts, firmware diffing, and Apple patch archaeology. | Apple Systems |
| Apple SDK and binary-inspection tools (`codesign`, `otool`, `nm`, `log`, `sysctl`) | Proof packet metadata, entitlements, build state, crash/log evidence, and local PoV helpers. | Apple Systems |
| Microsoft SandboxSecurityTools | LPAC and eligible sandbox proof setup. | Microsoft Systems |
| PowerShell, `whoami`, `Get-Process`, `icacls`, `reg` | Windows build, token, process, ACL, and registry evidence. | Microsoft Systems |

## Practical Install Order

1. Install Core first.
2. Add Source for source-heavy targets.
3. Add exactly one primary domain pack: Web, Binary, Cloud, Supply Chains, or Android.
4. Add Apple Systems or Microsoft Systems only when the program requires those proof or mitigation workflows.
