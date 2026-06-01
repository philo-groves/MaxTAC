---
name: maxtac-report-writer
description: Write MaxTAC vulnerability reports and campaign summaries from proofed systems findings. Use for kernel, driver, binary, crash, fuzzing, patch-diff, or open-source systems reports, remediation handoffs, bounty submissions, or proof packet summaries.
---

# MaxTAC Report Writer

Use this skill after a finding is `proofed` or when the user asks for a campaign summary. Base reports on ledger entries and proof packets, not discovery hunches.

## Report Shape

For each proofed finding include:

```text
Title:
Severity:
Confidence:
Target:
Affected versions/artifacts:
Vulnerability class:
Summary:
Attack scenario:
Preconditions:
Reproduction:
Expected behavior:
Actual behavior:
Impact:
Negative controls:
Root cause:
Fix:
Regression tests:
Evidence references:
Scope and safety notes:
```

## Systems-Specific Guidance

- For XNU: name the user-kernel interface, entitlement or sandbox assumptions, object lifetime, locking, and relevant mitigation effects.
- For Windows: name the driver, IOCTL/IRP/object boundary, caller privileges, pointer probing, ACL/token assumptions, and OS/build context.
- For binary findings: include artifact hash, architecture, symbols or offsets, patch diff facts, and static/runtime evidence.
- For fuzzing/crashes: include harness, sanitizer/debugger output, minimized input, deduplication notes, and root-cause lead.
- For open-source systems code: include file/function references, call path, attacker-controlled input, and patchable guard.

## Style

Lead with confirmed security impact. Keep exploit details minimal but sufficient for authorized triage. Redact secrets, tokens, customer data, and unnecessary machine-specific identifiers.

If evidence is not proofed, label it as a candidate or triage note rather than a vulnerability report.
