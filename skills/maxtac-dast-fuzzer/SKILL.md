---
name: maxtac-dast-fuzzer
description: Use fuzzing to dynamically discover vulnerability primitives in parsers, native libraries, binaries, kernels, protocols, APIs, web applications, browsers, mobile apps, and managed runtimes. Documented technologies include AFL++, libFuzzer, FuzzTest/Centipede, LibAFL, WinAFL, Honggfuzz, cargo-fuzz, Go fuzzing, Jazzer, Atheris, syzkaller, boofuzz, RESTler, Schemathesis, Nuclei, Burp Intruder, ZAP Fuzzer, ffuf, Fuzzilli, Domato, libprotobuf-mutator, Grammarinator, Nautilus, Radamsa, Android Monkey, ClusterFuzzLite, OSS-Fuzz, and FuzzBench.
---

# MaxTAC DAST Fuzzer
MaxTAC uses fuzzing to discover vulnerability primitives by repeatedly exercising a target with adversarial, semi-valid, or state-aware inputs and then proving the resulting behavior with reproducible evidence.

Only fuzz targets that are inside the authorized program scope. Prefer local, isolated, virtualized, or device-lab targets before any shared service. Do not run high-rate fuzzing against production or third-party infrastructure without explicit permission, rate limits, and cleanup rules.

## Fuzzing Strategy

Prefer the narrowest executable trust boundary with the strongest feedback signal:

1. Source or instrumented harness against the parser, RPC handler, deserializer, syscall, codec, or policy decision.
2. Binary-only harness with dynamic instrumentation, emulation, or snapshotting.
3. Stateful API or protocol fuzzer with an explicit model of authentication, resource creation, and cleanup.
4. Request, parameter, content, or UI fuzzing only when lower-level harnessing is unavailable.

Treat the fuzzer as a discovery engine, not the proof. For every signal, preserve the exact input or request sequence, minimize it, replay it outside the campaign, collect crash or logic evidence, and connect it to a security boundary.

Avoid spending campaign time on:

- Harnesses that mostly fuzz logging, CLI parsing, test scaffolding, or error paths.
- UI fuzzing when the vulnerable parser or API can be reached directly.
- Pure response-code or exception oracles when authorization, isolation, disclosure, or state corruption is the real property.
- Generated inputs that are syntactically valid but semantically impossible in the target system.

## Campaign Discipline

Build campaigns around target, generator, feedback, oracle, and evidence:

- **Target**: Identify the trust boundary, privilege boundary, parser, protocol state, or object lifetime transition under test.
- **Generator**: Choose mutation, grammar, schema, protobuf, stateful API sequence, or UI event generation based on what the target accepts.
- **Feedback**: Prefer coverage, comparison logging, sanitizer feedback, state coverage, data coverage, or protocol-state coverage when available.
- **Oracle**: Look for crashes, sanitizer findings, assertion failures, memory leaks, invariant breaks, authorization bypasses, state corruption, differential mismatches, and reproducible security impact.
- **Evidence**: Save corpus seeds, dictionaries, generated grammars, command lines, versions, target build hashes, minimized reproducers, debugger traces, logs, screenshots, and cleanup notes.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

## Native and Binary Fuzzers

### AFL++
Preferred default for native code and long-running vulnerability research campaigns when source, build flags, or binary-only instrumentation are available. Strongest fit for C/C++, parsers, codecs, file formats, libraries, command-line tools, and binaries that can be placed behind a fast harness. Use persistent mode, dictionaries, comparison logging, and sanitizers before increasing hardware.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

### libFuzzer
Preferred when the project already has or can easily accept an in-process `LLVMFuzzerTestOneInput` harness. Good for library-level C/C++ targets, regression fuzzing, and cross-engine harness reuse. Use with LLVM sanitizers. Do not expect major new libFuzzer features; its harness ABI remains valuable and widely reusable.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

### FuzzTest / Centipede
Preferred for C++ projects that benefit from property-style, typed-domain fuzz tests, especially Bazel or GoogleTest-adjacent code. Use for semantic invariants, round-trip properties, and APIs that are easier to model with typed values than raw byte streams. Treat standalone Centipede references as moving under FuzzTest.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

### LibAFL
Preferred when an off-the-shelf fuzzer does not match the target: unusual instrumentation, emulation, snapshots, custom schedulers, nonstandard feedback, embedded targets, or hybrid research. Avoid it for routine harness fuzzing unless the extra control is needed.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

### WinAFL
Preferred for Windows binary-only targets that need DynamoRIO-style instrumentation, especially closed-source desktop libraries and file parsers. Try source instrumentation or AFL++ FRIDA/QEMU/Wine paths first when they are practical.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

### Honggfuzz
Useful when a target already has honggfuzz integration, when its multi-process model is convenient, or when hardware/software coverage modes fit the environment. Prefer AFL++ or libFuzzer when their harness ecosystem is already present.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

## Language Runtime Fuzzers

### cargo-fuzz
Preferred for Rust crates using Cargo. It invokes libFuzzer through Rust tooling and is the normal first choice for Rust library fuzzing. Use invariants, `arbitrary`-style input generation, and sanitizer-enabled builds when supported.

See: `<skill-dir>/references/language-runtime-fuzzing.md`

### Go Native Fuzzing
Preferred for Go modules because fuzzing is built into the Go toolchain. Use for parsers, decoders, validators, auth policy helpers, URL/path logic, and protocol state helpers. Preserve failing inputs from `testdata/fuzz`.

See: `<skill-dir>/references/language-runtime-fuzzing.md`

### Jazzer
Preferred for JVM targets, including Java, Kotlin, Scala, and JVM-based parsers or deserializers. Use it for bytecode-level coverage-guided fuzzing and pair crash or exception findings with security-specific oracles.

See: `<skill-dir>/references/language-runtime-fuzzing.md`

### Atheris
Preferred for Python code and CPython native extensions when coverage-guided fuzzing is needed. Best targets are parsers, validators, serializers, C-extension bindings, and logic that can be isolated from network and wall-clock dependencies.

See: `<skill-dir>/references/language-runtime-fuzzing.md`

## API and Web Fuzzers

### RESTler
Preferred for stateful REST APIs with OpenAPI specifications where producer-consumer dependencies, resource lifecycles, and request sequences matter. Use when single-request fuzzing is too shallow to reach meaningful service state.

See: `<skill-dir>/references/web-api-fuzzing.md`

### Schemathesis
Preferred for fast schema-based OpenAPI or GraphQL fuzzing, CI integration, and minimal reproducible `curl` evidence. Use it early to discover schema mismatches, server errors, stateful flow gaps, and property violations.

See: `<skill-dir>/references/web-api-fuzzing.md`

### Nuclei
Preferred for template-driven HTTP fuzzing and broad, repeatable web DAST over captured traffic, crawled endpoints, or known request shapes. Use preconditions and matchers to keep templates high-signal. Treat Nuclei output as a lead until manually reproduced.

See: `<skill-dir>/references/web-api-fuzzing.md`

### Burp Intruder
Preferred for manual, session-aware HTTP request fuzzing where human-guided payload placement, cookies, CSRF state, and response comparison matter. Use for validation, not just volume.

See: `<skill-dir>/references/web-api-fuzzing.md`

### ZAP Fuzzer
Preferred open-source GUI option for HTTP request fuzzing with custom payloads, scripts, and processors. Use when Burp is unavailable or an open workflow is required.

See: `<skill-dir>/references/web-api-fuzzing.md`

### ffuf
Preferred for fast content discovery, parameter discovery, virtual-host discovery, and controlled value fuzzing. It is not a vulnerability oracle by itself; use filters, baselines, and follow-up proofing.

See: `<skill-dir>/references/web-api-fuzzing.md`

## Protocol, Browser, Mobile, and System Fuzzers

### syzkaller
Preferred for kernels, syscall surfaces, drivers, and OS services. Best fit when the target can run under a managed VM/device farm with coverage, sanitizers, crash collection, and reproducer minimization.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

### boofuzz
Preferred for stateful network, serial, industrial, embedded, or custom binary protocols when a researcher can model protocol messages and transitions. Use monitors, reset hooks, and session graphs so crashes are attributable.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

### Fuzzilli
Preferred for JavaScript engines and dynamic language interpreters where the generated program needs to stay semantically rich enough to reach JIT, optimizer, and runtime edges.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

### Domato
Preferred for DOM, HTML, CSS, and browser-engine stress generation. Use with browser crash monitors, instrumented builds when possible, and a reproducible reduction workflow.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

### Android Native and UI Fuzzing
Prefer AOSP/libFuzzer-style native component fuzzing for Android libraries and system components. Use Android Monkey only as repeatable UI stress to shake out lifecycle crashes; do not rely on it for deep vulnerability discovery.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

## Structure-Aware and Corpus Tools

### libprotobuf-mutator
Preferred when a target consumes structured data that can be modeled as protobufs or an intermediate schema. Use it to keep inputs semantically valid while coverage-guided engines explore deeper parser and state logic.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

### Nautilus
Preferred when grammar-aware and coverage-guided fuzzing are both needed for highly structured text or language inputs.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

### Grammarinator
Preferred when ANTLR grammars exist or can be created and generation quality matters more than raw coverage feedback. Pair with a coverage-guided engine or corpus feedback when possible.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

### Radamsa
Preferred for quick black-box mutation, seed corpus expansion, protocol smoke testing, and payload generation when no harness exists yet. Use it as a bridge into a stronger campaign, not as the final campaign if instrumentation is available.

See: `<skill-dir>/references/protocol-and-system-fuzzing.md`

## Continuous Fuzzing and Evaluation

### OSS-Fuzz
Preferred for eligible open-source projects that need long-running, scalable continuous fuzzing with sanitizers and crash reporting.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

### ClusterFuzzLite
Preferred for repository-owned CI fuzzing in pull requests, batch jobs, coverage jobs, and corpus pruning. Use when the project cannot or should not go directly to OSS-Fuzz.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

### FuzzBench
Use for evaluating fuzzer research or comparing engine changes under reproducible benchmarks. Do not treat benchmark ranking as a substitute for target-specific campaign results.

See: `<skill-dir>/references/coverage-guided-fuzzing.md`

## Evidence and Handoff

For every meaningful fuzzing result, preserve:

- Authorization scope, rate limits, test environment, and target version.
- Tool name, exact version, command line, environment variables, build flags, sanitizer flags, and instrumentation mode.
- Harness source, generated grammar, schema, model, request template, or UI script.
- Seed corpus, minimized corpus, dictionaries, generated inputs, and corpus hashes when practical.
- Crash input, minimized reproducer, replay command, debugger output, sanitizer report, stack trace, logs, core dump, and screenshots or recordings when UI state matters.
- For APIs, the full request sequence, auth context, resource IDs, cleanup actions, HAR/curl reproducer, response bodies, and evidence that the behavior crosses a security boundary.
- For logic bugs, the invariant, expected behavior, observed behavior, replay stability, and proof that the fuzzer did not create an impossible state.

Use `maxtac-dast-debugger` for crash replay, runtime instrumentation, browser debugging, and mobile device interaction. Use `maxtac-dast-virtualization` for isolated campaign environments.
