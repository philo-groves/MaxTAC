# Coverage-Guided Fuzzing

Use this reference for source-available native code, binary-only native code,
continuous fuzzing, sanitizer-driven crash discovery, and fuzzer selection.

Prefer coverage-guided harness fuzzing whenever the target can be built,
instrumented, wrapped, emulated, or debug-instrumented. Black-box request and UI
fuzzing should be a fallback or reconnaissance layer, not the first choice for
deep vulnerability discovery.

## Current Tool Selection

Use AFL++ as the default campaign engine for native targets when:

- The target can be compiled with AFL++ instrumentation.
- Persistent mode can be added or the target can be converted into a library
  harness.
- Binary-only QEMU, FRIDA, Wine, Unicorn, or Nyx modes are needed.
- Comparison logging, dictionaries, LAF/CMPLG, or many synchronized workers are
  likely to matter.

Use libFuzzer when:

- A clean in-process harness is easy to write.
- The project already uses LLVM sanitizers or OSS-Fuzz-style harnesses.
- Corpus minimization, local reproduction, and unit-level regression are more
  important than AFL++ campaign orchestration.
- The same `LLVMFuzzerTestOneInput` harness should be reusable by AFL++ or
  honggfuzz.

Use FuzzTest when:

- The target is C++ and the natural oracle is a typed property, not raw bytes.
- The codebase already uses Bazel, GoogleTest, or property-style tests.
- The goal is to encode invariants such as round-trip, normalization,
  authorization equivalence, parser/printer stability, or idempotence.

Use LibAFL when:

- The target needs a custom fuzzer architecture, emulator, snapshot, scheduler,
  mutator, feedback channel, or hybrid design.
- The ordinary AFL++ or libFuzzer execution model does not match the target.
- The extra engineering cost is justified by target value or target weirdness.

Use WinAFL when:

- The target is Windows-only and binary-only.
- A target function can be selected by module and offset.
- DynamoRIO instrumentation is acceptable and a process or persistent harness is
  practical.

Use honggfuzz when:

- The target already has honggfuzz support.
- Multi-process execution, hardware feedback, or its crash handling fits the
  environment.
- AFL++ or libFuzzer support is absent and adding it is not worth the time.

Use OSS-Fuzz or ClusterFuzzLite for continuous fuzzing. Use FuzzBench for
evaluating fuzzing research, not for deciding campaign quality on a specific
MaxTAC target.

## Harness Rules That Matter

Fuzz the smallest deterministic function that crosses a trust boundary. Good
targets include parsers, deserializers, decompression, image/font/media codecs,
archive readers, policy parsers, path normalization, ACL checks, IPC decode,
RPC dispatch, certificate parsing, firmware blob parsing, bytecode loading, and
driver/user-client methods.

Shape the harness so each iteration:

- Starts from a clean enough state.
- Accepts empty, huge, malformed, duplicate, and partial inputs.
- Does not call `exit()`, `abort()`, `sleep()`, network services, or wall-clock
  dependent logic except when those calls are the explicit target.
- Does not mask the vulnerability with broad exception handlers.
- Does not create persistent filesystem, database, cache, account, or service
  state unless cleanup is built into the harness.
- Runs quickly enough that instrumentation overhead still leaves useful
  throughput.

Persistent mode usually beats more cores. Before adding hardware, improve the
harness, seed corpus, dictionary, comparison instrumentation, and reset logic.

## Sanitizer Matrix

Use sanitizer builds as bug oracles:

- ASan: heap, stack, global out-of-bounds, use-after-free, and related memory
  safety issues.
- UBSan: signed overflow, shifts, invalid enum, nullability, misalignment, and
  other undefined behavior that can turn into memory corruption.
- LSan: leaks that indicate missing teardown, parser-owned object retention, or
  resource exhaustion. Avoid over-reporting harmless one-time process leaks.
- MSan: uninitialized reads, especially parser state and copyout paths. Run
  separately because it requires instrumented dependencies.
- TSan: races. Run separately and expect lower throughput and more triage work.
- KASAN/KMSAN/KCSAN/KFENCE: kernel campaigns, usually with syzkaller or
  subsystem-specific harnesses.
- HWASan: useful on supported AArch64 targets.

Do not report a sanitizer finding until it reproduces with a minimal input and
the stack trace reaches security-relevant target code.

## Corpus and Mutation Discipline

Start with small, diverse, valid examples and a few intentionally invalid
examples. High-quality seeds beat large undifferentiated corpora.

Minimize corpora before long runs and after importing external test suites.
Keep:

- Original seed corpus.
- Minimized working corpus.
- Crash corpus.
- Regression corpus after proof.
- Dictionary files and grammar/protobuf schemas.

Add dictionaries for magic bytes, tags, keywords, enum names, field labels,
protocol verbs, file signatures, lengths, separators, and values observed in
source or traces. Comparison logging and data-coverage-style signals are useful
when branch coverage stalls behind constants, checksums, keywords, embedded
interpreters, or protocol automata.

Reuse old crashes against new versions. Crash reuse often finds incomplete
fixes and variant regressions faster than a fresh campaign.

## Binary-Only Campaign Notes

For AFL++ binary-only targets, try in this order when practical:

1. FRIDA or QEMU persistent mode with high stability.
2. FRIDA or QEMU with an entrypoint near the target parser or dispatch loop.
3. Instrumented shared-library harness with library range selection.
4. Wine/QEMU for Win32 PE targets.
5. Unicorn or a custom LibAFL harness for firmware or lifted execution.
6. WinAFL when DynamoRIO and Windows-local execution are the most practical
   path.

For binary-only work, record:

- Module names, image bases, target offsets, ASLR state, and bitness.
- Entry point or function offset selected for fuzzing.
- Coverage mode, instrumentation ranges, excluded modules, and persistent-loop
  stability.
- Whether the harness runs in-process, out-of-process, forkserver, snapshot, or
  emulation mode.

Use the debugger skill to replay crashes with symbols, breakpoints, heap
instrumentation, and memory inspection.

## Failure Modes

No new coverage:

- The harness does not reach the target.
- Inputs are rejected before the interesting parser.
- Checksums, lengths, signatures, magic values, or version fields need a
  dictionary, custom mutator, or structure-aware model.
- Coverage is attached to the wrong module or the wrong process.

Low execs/sec:

- Startup dominates execution.
- The target performs I/O, network, sleeps, logging, or expensive setup per
  iteration.
- Sanitizer or emulator overhead is acceptable only if the bug class justifies
  it.
- Persistent mode or snapshots should be added.

Unstable coverage:

- Global state, randomization, threads, time, filesystem state, caches, signal
  handlers, ASLR-sensitive code, or flaky dependencies are leaking across
  iterations.

Crashes do not reproduce:

- The minimized input depends on environment, corpus state, previous iteration
  state, temp files, time, thread scheduling, heap layout, or sanitizer options.
- Re-run in a fresh process, then under a debugger, then under an unsanitized or
  differently sanitized build as needed.

## Evidence Checklist

Collect:

- Tool versions, target version, compiler version, sanitizer runtime version,
  and host OS.
- Build commands, fuzzer command, environment variables, timeouts, memory
  limits, CPU count, and campaign duration.
- Harness source, instrumentation mode, persistent-mode details, and reset
  model.
- Seeds, minimized corpus, dictionaries, schemas, generated inputs, and
  minimized crash input.
- Crash stack, sanitizer report, core dump, debugger replay, module offsets,
  and source or disassembly notes.
- Proof that the crash or invariant break crosses an authorized security
  boundary.

## References

- https://aflplus.plus/docs/fuzzing_in_depth/
- https://aflplus.plus/docs/fuzzing_binary-only_targets/
- https://llvm.org/docs/LibFuzzer.html
- https://github.com/google/fuzztest
- https://aflplus.plus/libafl-book/introduction.html
- https://github.com/googleprojectzero/winafl
- https://github.com/google/honggfuzz
- https://clang.llvm.org/docs/AddressSanitizer.html
- https://google.github.io/oss-fuzz/
- https://google.github.io/clusterfuzzlite/
- https://google.github.io/fuzzbench/
- https://www.usenix.org/conference/usenixsecurity24/presentation/wang-mingzhe
- https://security.googleblog.com/2024/11/leveling-up-fuzzing-finding-more.html
