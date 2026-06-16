# Protocol, Browser, Mobile, and System Fuzzing

Use this reference when the fuzz target is not a simple library harness:
kernels, syscalls, network protocols, browser engines, mobile apps, DOM, UI
stress, firmware-style execution, or structured languages.

## syzkaller

Use syzkaller for syscall, kernel, driver, and OS service fuzzing. It is most
useful when:

- The target OS can run in disposable VMs or lab devices.
- Coverage feedback and kernel sanitizers are available.
- The syscall or IOCTL surface can be described, extended, or scoped.
- Crash reproduction and minimization are more valuable than raw request volume.

Good syzkaller campaigns require:

- A kernel build with the right coverage and sanitizer options.
- VM/device reset automation.
- Scoped syscall descriptions or subsystem focus.
- Reproducer preservation in both syz and C forms when available.
- A triage path through kernel logs, crash dumps, and source or symbols.

Watch for false signals from unsupported hardware, flaky VMs, debug asserts,
known upstream bugs, and crashes caused by impossible privilege context.

## boofuzz

Use boofuzz for stateful protocol fuzzing when the researcher can model message
structure and session transitions.

Model:

- Handshake, authentication, negotiation, and teardown.
- Message length fields, checksums, sequence numbers, IDs, and capability flags.
- One request per state transition when possible.
- Reset hooks that restore the service after timeouts or crashes.
- Monitors for process death, logs, serial output, network disconnects, and
  device health.

boofuzz is strongest when protocol knowledge is high. If the grammar is weak,
start with packet captures, a reference client, debug logs, or Frida hooks to
learn valid state transitions before mutating.

## Browser and JavaScript Engine Fuzzing

Use Fuzzilli for JavaScript engines and dynamic language interpreters. It is
designed to generate semantically rich programs through an intermediate
language so the campaign can reach parser, runtime, optimizer, JIT, and garbage
collector behavior.

Use Domato for DOM/HTML/CSS/browser-engine stress where generated pages and
scripts should exercise web platform APIs.

For browser campaigns:

- Prefer instrumented debug or fuzzing builds when available.
- Capture browser version, revision, build args, sanitizer args, feature flags,
  and runtime flags.
- Run with crash dump collection and console/log capture.
- Distinguish renderer crash, browser crash, GPU crash, sandbox violation,
  assertion, timeout, and out-of-memory.
- Reduce generated HTML/JS/CSS before proofing.
- Replay under CDP, WebDriver BiDi, or WebKit tooling when UI/frame state
  matters.

Use the `maxtac-dast-debugger` CDP, WebDriver BiDi, and WebKit references for
browser replay and evidence capture.

## Android and Mobile Fuzzing

Prefer native or service-level fuzzing over random UI event fuzzing:

- For Android platform/native components, use AOSP libFuzzer integration where
  possible.
- For app native libraries, isolate JNI or native parser boundaries behind a
  host or device harness.
- For Binder, intents, content providers, deep links, file import, and custom
  URL schemes, model the smallest message or invocation boundary.
- Use Frida to observe argument shapes, extract seeds, bypass non-security
  harness blockers, or attach crash context. Keep instrumentation effects out
  of final proof when possible.

Use Android Monkey only for repeatable UI stress, lifecycle crashes, and smoke
coverage. It sends pseudo-random UI and system events; it is usually too shallow
for deep parser or authorization vulnerability discovery unless paired with a
targeted setup state and log/crash oracle.

For iOS app work, use first-party UI automation such as XCUITest to reach
states, but fuzz the underlying parser, file import, URL scheme, network API,
or native boundary directly whenever possible.

## Structure-Aware Fuzzing

Use structure-aware fuzzing when raw mutation cannot pass syntax, checksums,
lengths, semantic validators, or protocol state gates.

Use libprotobuf-mutator when:

- The target already uses protobufs.
- The input can be represented as a protobuf schema.
- A custom bridge can serialize protobuf messages into the target format.
- Coverage-guided engines need semantically valid inputs.

Use Nautilus when:

- A grammar is available and coverage feedback should guide grammar mutations.
- Deep parser bugs require inputs that stay semi-valid.

Use Grammarinator when:

- ANTLR grammars exist or can be written.
- Generating syntactically valid test cases matters more than engine-specific
  coverage integration.

Use Radamsa when:

- A quick black-box mutator is needed before a harness exists.
- Existing samples can be expanded into mutated files or payload streams.
- The goal is seed generation, smoke testing, or reproducer variation.

## LLM-Assisted Fuzzing

Use LLMs as accelerators for harness and generator work, not as final proof
systems. Productive uses include:

- Drafting harnesses from public APIs, tests, and examples.
- Turning specifications into grammar or protobuf models.
- Inferring protocol state machines from docs and traces.
- Generating seed corpora for structured formats.
- Suggesting invariants for managed runtimes and API workflows.
- Mutating generator code for non-textual formats.

Validate every generated harness or grammar with coverage, replay, minimization,
and manual review. A generated model can overfit documentation, skip dangerous
states, or create impossible inputs that do not correspond to attacker reach.

## Evidence Checklist

Collect:

- Target firmware, kernel, browser, app, protocol, or service version.
- Build flags, sanitizer flags, device/VM image, emulator/simulator/device
  identity, and reset procedure.
- Protocol model, grammar, syzlang additions, protobuf schema, generated
  corpus, or UI script.
- Crash logs, kernel logs, browser dumps, device logs, network captures, serial
  output, screenshots, and minimized reproducers.
- State setup required before replay, including credentials, device pairing,
  profile, feature flags, and environmental dependencies.

## References

- https://github.com/google/syzkaller
- https://boofuzz.readthedocs.io/
- https://boofuzz.readthedocs.io/en/stable/user/quickstart.html
- https://github.com/googleprojectzero/fuzzilli
- https://github.com/googleprojectzero/domato
- https://source.android.com/docs/security/test/libfuzzer
- https://developer.android.com/studio/test/other-testing-tools/monkey
- https://developer.android.com/studio/test/monkeyrunner
- https://developer.apple.com/documentation/xcuiautomation
- https://github.com/google/libprotobuf-mutator
- https://github.com/google/fuzzing/blob/master/docs/structure-aware-fuzzing.md
- https://github.com/nautilus-fuzz/nautilus
- https://grammarinator.readthedocs.io/en/latest/guide/fuzzer_building.html
- https://gitlab.com/akihe/radamsa
- https://www.usenix.org/conference/usenixsecurity25/presentation/zhang-kunpeng
- https://arxiv.org/html/2402.00350v3
