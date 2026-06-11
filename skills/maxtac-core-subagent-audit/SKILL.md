---
name: maxtac-core-subagent-audit
description: Flows for working with auditor subagents to perform specialized vulnerability scanning. Uses a mix of main and subagent reasoning for maximum vulnerabilty research coverage.
---

# MaxTAC Core Subagent Audit
Use this skill for spawning auditor subagents. Each auditor subagent specializes in a vulnerability of a specific type. Auditor subagents are generally ready-only so they do not conflict with each other; the exclusions are per-auditor evidence and other conflict-free files. Each audit is stored in a `data/maxtac/audits/<audit-id>` directory, where `<audit-id>` is a generated ID.

## Model Selection

All auditor subagents use GPT 5.5 xhigh due to the reasoning requirement.

## A Shared Responsibility
A shared responsibility exists between the main agent and subagent. The main agent must reason about the best vulnerability specialist for the target, while the subagent must act independently as that specialist. The main agent must also carefully write subagent prompts so they are durable enough to surface findings, but not so complex to cause run-on agents.

## Audit Flow
1. Main agent generates a unique audit ID and creates `data/maxtac/audits/<audit-id>/`.
2. Main agent accepts one or more hypotheses from another phase, or uses creative thinking to hypothesize. For each hypothesis, generate unique subagent ID for it. There is one subagent per hypothesis. Prefer the format from `<skill-dir>/assets/hypothesis.template.md` and fill in the missing sections; rewrite accepted hypotheses to match this format if needed.
3. Persist each raw hypothesis to `data/maxtac/audits/<audit-id>/<subagent-id>/hypothesis.md`, then spawn each subagent with the hypothesis as a prompt; include no session history.
4. As each subagent completes its audit, the results are stored in `data/maxtac/audits/<audit-id>/<subagent-id>/evidence.md`. Prefer the format from `<skill-dir>/assets/evidence.template.md` and fill in the missing sections. Other supporting evidence files may be included in the same directory.
5. Main agent analyzes subagent results as they appear, not waiting for every subagent.

## Vulnerability Specialists

These are only a few examples of the types of specialists that may be spawned.

- Time-of-Check to Time-of-Use (TOCTOU): a system checks the state of a resource, but that state changes before the system uses it.
- Use-After-Free (UAF): a program continues to use a pointer after the memory it references has been deleted or freed.
- Out-of-bounds Read: a program reads data past the end, or before the beginning, of the intended buffer.
- Improper Neutralization of Special Elements used in an OS Command: a program constructs all or part of an OS command using externally-influenced input from an upstream component, but it does not neutralize or incorrectly neutralizes special elements that could modify the intended OS command when it is sent to a downstream component.
- Heap-based Buffer Overflow: the buffer that can be overwritten is allocated in the heap portion of memory, generally meaning that the buffer was allocated using a routine such as malloc().
- Deserialization of Untrusted Data: a program deserializes untrusted data without sufficiently ensuring that the resulting data will be valid.
- Business Logic Flaw: code executes correctly, but the process flow can be manipulated (e.g., bypassing a step in an account creation process).
- Chained Vulnerabilities: several low-severity, non-threatening flaws can be combined by an attacker to form a severe compromise.
- Authentication Flaws: role-based permission errors and access controls that do not trigger code execution errors.
- Hidden or Internal Assets: exposed test environments, shadow IT, or undocumented API endpoints that bypass a scanner.
- Heap Grooming: an application's dynamic memory management can be manipulated to create a predictable, advantageous memory layout
- Jump-Oriented Programming (JOP): advanced code-reuse attack that bypasses modern hardware memory protections without relying on the stack. It functions by chaining together small snippets of existing code (gadgets) ending in indirect jumps or calls.
- Stack Pivoting: a technique where an attacker redirects the program’s stack pointer (ESP in 32-bit, RSP in 64-bit) to an attacker-controlled memory location, such as the heap
