# Language Runtime Fuzzing

Use this reference for Go, Rust, JVM, Python, and other managed runtime fuzzing.
The strongest findings usually come from security-specific invariants rather
than raw crashes.

## Runtime Strategy

For managed runtimes, define explicit oracles:

- Round-trip: parse, serialize, parse again, and compare normalized structure.
- Differential: compare two implementations, two versions, or two execution
  modes.
- Authorization: mutate subject, resource, scope, tenant, role, token, and
  policy fields.
- Canonicalization: compare path, URL, Unicode, encoding, case-folding,
  escaping, and normalization behavior.
- Resource safety: bound CPU, memory, recursion depth, decompression expansion,
  database queries, and background jobs.
- Error safety: malformed inputs must fail closed without leaking secrets,
  stack traces, paths, or internal IDs.

Treat uncaught exceptions as leads. Prove impact by tying the failure to
security behavior, denial of service, parser confusion, data disclosure,
sandbox escape, or policy bypass.

## Go Native Fuzzing

Use Go native fuzzing for Go modules. Good targets include:

- URL, path, and filesystem normalization.
- Encoding, compression, archive, image, and document parsers.
- Token, JWT, certificate, or crypto-adjacent parsers.
- ACL, RBAC, ABAC, and policy-evaluation helpers.
- Protocol decoders and state helpers.

Preserve:

- `FuzzXxx` test source.
- Seed corpus and failing files under `testdata/fuzz`.
- `go version`, module version, `go test -fuzz` command, and fuzz cache state.
- Any custom invariants or differential reference implementation.

## Rust cargo-fuzz

Use `cargo-fuzz` for Rust crates using Cargo. Prefer:

- Small library-level fuzz targets over CLI fuzzing.
- `arbitrary` or structure-aware input generation when byte slices are too
  shallow.
- Round-trip, differential, and panic-safety properties.
- Sanitizer-enabled builds for unsafe code, FFI, parser internals, and C/C++
  dependencies.

Keep minimized crash artifacts in the fuzz artifacts directory and replay with
the exact target name and feature flags.

## Jazzer for JVM

Use Jazzer for Java, Kotlin, Scala, and other JVM targets. Strong targets:

- Deserialization and parser libraries.
- Template engines and expression languages.
- XML, JSON, YAML, ASN.1, protobuf, archive, and image handling.
- Auth and policy libraries with pure or mostly pure entrypoints.
- JNI or native-backed Java APIs when paired with native sanitizers where
  possible.

Jazzer findings often need security triage because JVM exceptions are common.
Use custom bug detectors or assertions to turn invariant violations into
actionable reports.

Record classpath, build tool, JVM version, Jazzer version, target class,
instrumentation include/exclude settings, and reproducer input.

## Atheris for Python

Use Atheris for Python code and CPython native extensions. Strong targets:

- Parsers, validators, encoders, decoders, importers, and file readers.
- Python wrappers around C/C++ libraries.
- Security-sensitive canonicalization and policy helpers.
- JSON/YAML/TOML/XML/archive/image/media libraries.

For pure Python, focus on invariant violations, uncaught exceptions, resource
exhaustion, and differential behavior. For native extensions, pair Atheris with
ASan or UBSan when practical.

Record Python version, Atheris version, package versions, native extension build
flags, sanitizer options, and minimized input.

## Managed Runtime Failure Modes

Low-value exceptions:

- The harness calls a public API with impossible object combinations.
- A library documents that malformed input raises that exact exception.
- The failure is a test-only assertion or intentionally unsupported feature.

High-value signals:

- One input crashes the interpreter, VM, or native extension.
- Parser accepts two conflicting interpretations of the same security input.
- Canonicalization differs across validation and enforcement.
- A supposedly isolated tenant, role, user, or sandbox context influences
  another.
- Resource use grows superlinearly from small inputs.
- Exception output leaks secrets, filesystem paths, credentials, internal
  service names, or object IDs.

## Evidence Checklist

Collect:

- Runtime version, package versions, dependency lockfile, and target commit.
- Fuzzer version, command, corpus, failing input, and minimized reproducer.
- Harness source and property definition.
- Crash, exception, panic, assertion, differential mismatch, or resource metric.
- Manual replay in a normal test runner when possible.
- Explanation of why the input is attacker-reachable or crosses a security
  boundary.

## References

- https://go.dev/doc/security/fuzz/
- https://rust-fuzz.github.io/book/cargo-fuzz.html
- https://github.com/rust-fuzz/cargo-fuzz
- https://github.com/codeintelligencetesting/jazzer
- https://security.googleblog.com/2021/03/fuzzing-java-in-oss-fuzz.html
- https://github.com/google/atheris
- https://google.github.io/oss-fuzz/getting-started/new-project-guide/python-lang/
- https://llvm.org/docs/LibFuzzer.html
