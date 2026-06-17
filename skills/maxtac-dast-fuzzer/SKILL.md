---
name: maxtac-dast-fuzzer
description: "Use this skill when dynamic testing needs fuzzing for parsers, binaries, kernels, protocols, APIs, web apps, browsers, mobile apps, managed runtimes, coverage-guided engines, grammar fuzzers, or harness selection."
---

# MaxTAC DAST Fuzzer
Use fuzzing to discover vulnerability primitives; prove results through minimized replay and security-boundary evidence.

Only fuzz targets that are inside the authorized program scope. Prefer local, isolated, virtualized, or device-lab targets before any shared service. Do not run high-rate fuzzing against production or third-party infrastructure without explicit permission, rate limits, and cleanup rules.

## Fuzzing Persistence
All fuzzing inputs, scripts, and artifacts should be saved in the `fuzz/` directory of the research workspace for easy pruning, evidence collection, and handoff. This includes harnesses, generated grammars, seed corpus, dictionaries, command lines, environment variables, build flags, sanitizer flags, target versions, crash inputs, minimized reproducers, replay commands, debugger output, sanitizer reports, stack traces, logs, core dumps, screenshots or recordings when UI state matters, and for APIs the full request sequence with auth context and resource IDs.

Use `python3 <skill-dir>/scripts/fuzz-campaign.py` to create and lint fuzzing evidence bundles instead of tracking campaign facts in loose notes.

MaxTAC MCP convention: use `fuzz_campaign` before `scripts/fuzz-campaign.py` when available; actions mirror the script (`init`, `add-run`, `lint`, `summary`).

Initialize a campaign under `<workspace-root>/fuzz/<campaign-id>/`:

```
python3 <skill-dir>/scripts/fuzz-campaign.py init \
  --target "parser component" \
  --target-version "1.2.3 build 456" \
  --tool AFL++ \
  --version-command "afl-fuzz -V" \
  --scope "authorized local lab target" \
  --environment "Windows VM snapshot abc123" \
  --rate-limits "local only" \
  --instrumentation "ASan + coverage" \
  --command "afl-fuzz -i seeds -o out -- ./harness @@" \
  --harness ./harness.cc \
  --seed-corpus ./seeds
```

Attach a reproduced crash or logic/API result:

```
python3 <skill-dir>/scripts/fuzz-campaign.py add-run fuzz-20260616T000000Z-abc123 \
  --kind crash \
  --replay-command "./harness crash.min" \
  --crash-input ./crash.raw \
  --minimized-reproducer ./crash.min \
  --sanitizer-report ./asan.txt \
  --stack-trace ./stack.txt
```

Before handoff, run:

```
python3 <skill-dir>/scripts/fuzz-campaign.py lint fuzz-20260616T000000Z-abc123 --kind crash --strict
python3 <skill-dir>/scripts/fuzz-campaign.py summary fuzz-20260616T000000Z-abc123
```

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

## Tool Selection

Read only the reference that matches the target and generator. Use the table as routing, not as a substitute for harness design.

| Target shape | Prefer | Reference |
| --- | --- | --- |
| Native parser, codec, library, CLI, or binary with source/build flags | AFL++, libFuzzer, FuzzTest | `<skill-dir>/references/coverage-guided-fuzzing.md` |
| Native target needing custom instrumentation, emulation, snapshots, or schedulers | LibAFL | `<skill-dir>/references/coverage-guided-fuzzing.md` |
| Windows binary-only target | WinAFL or AFL++ FRIDA/QEMU/Wine path | `<skill-dir>/references/coverage-guided-fuzzing.md` |
| Existing honggfuzz integration or convenient multi-process campaign | Honggfuzz | `<skill-dir>/references/coverage-guided-fuzzing.md` |
| Rust, Go, JVM, Python, or CPython extension target | cargo-fuzz, Go fuzzing, Jazzer, Atheris | `<skill-dir>/references/language-runtime-fuzzing.md` |
| Stateful REST/OpenAPI or schema-backed API | RESTler or Schemathesis | `<skill-dir>/references/web-api-fuzzing.md` |
| Captured HTTP traffic, templates, or manual session-aware request fuzzing | Nuclei, Burp Intruder, ZAP Fuzzer, ffuf | `<skill-dir>/references/web-api-fuzzing.md` |
| Kernel, syscall, driver, OS service, custom protocol, or browser engine | syzkaller, boofuzz, Fuzzilli, Domato | `<skill-dir>/references/protocol-and-system-fuzzing.md` |
| Android native component or repeatable UI stress | AOSP/libFuzzer-style harnesses or Android Monkey | `<skill-dir>/references/protocol-and-system-fuzzing.md` |
| Structured text, protobuf-like data, grammar, or seed expansion | libprotobuf-mutator, Nautilus, Grammarinator, Radamsa | `<skill-dir>/references/protocol-and-system-fuzzing.md` |
| Continuous fuzzing, CI, or fuzzer evaluation | OSS-Fuzz, ClusterFuzzLite, FuzzBench | `<skill-dir>/references/coverage-guided-fuzzing.md` |

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
