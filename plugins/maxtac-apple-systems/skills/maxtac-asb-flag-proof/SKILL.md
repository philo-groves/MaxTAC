---
name: maxtac-asb-flag-proof
description: "Use this skill when an Apple Security Bounty chain needs target-flag proof for register control, arbitrary read/write, arbitrary code execution, or TCC modification on iOS, iPadOS, macOS, tvOS, visionOS, or watchOS."
---

# MaxTAC ASB Flag Proof
Use this skill when an Apple chain requires objective proof of a vulnerability that results in register control, arbitrary read/write, arbitrary code execution, or TCC modification. Do not use this skill for primitive findings; it is only be used with chains. Apple provides and requires target flags to prove these scenarios on iOS, iPadOS, macOS, tvOS, visionOS, and watchOS.

## Types of Target Flags
- Commpage Target Flag: provides precise addresses and values to use in the proof of vulnerability (PoV), resulting in predictable crash logs that clearly demonstrate achieving exploit primitives in userspace and kernel.
- Transparency, Consent, and Control (TCC) Target Flag: allows to easily demonstrate write access to the per-user or system TCC database and confirm whether the PoV has fully compromised TCC.

## Commpage Target Flag
Many exploits begin by finding primitives of three fundamental levels of control:
1. Register control: Partially or fully control the value in one or more registers in the CPU.
2. Arbitrary read or write: Read and/or write at an attacker-chosen address.
3. Code execution: Execute attacker-controlled code.

The system selects random numbers at boot and stores them in the commpage — a stable section of memory that can be read at the same address from any process. To demonstrate exploitability, use these values in the commpage as the contents to write into a register, the address to read from or write to, or the address to which to jump, from an attacker-controlled process.

```
// Apple Security Bounty random values
#define _COMM_PAGE_ASB_TARGET_VALUE         (_COMM_PAGE_START_ADDRESS+0x320)        // uint64_t for random value
#define _COMM_PAGE_ASB_TARGET_ADDRESS       (_COMM_PAGE_START_ADDRESS+0x328)        // uint64_t for random target address
#define _COMM_PAGE_ASB_TARGET_KERN_VALUE    (_COMM_PAGE_START_ADDRESS+0x330)        // uint64_t for random kernel value
#define _COMM_PAGE_ASB_TARGET_KERN_ADDRESS  (_COMM_PAGE_START_ADDRESS+0x338)        // uint64_t for random kernel target address
```

To demonstrate any exploit primitive with the Commpage Target Flag, the PoV should crash and produce a crash log. Based on a quick inspection of register state, the crash log exposes the level of control the PoV achieved.

Here’s an example crash log from an arbitrary read from the target address `0x08ad752109466b05` as identified with the exception address and register x8 control: `assets/arbitrary-read-example.crash`

To report of kernel or user-level privilege escalation, include a PoV using the Commpage Target Flag and an accompanying crash log to prove the capability demonstrated — and qualify for the maximum reward.

Not every crash is exploitable. For example, Apple generally does not reward NULL-pointer dereferences or assertion failures, even if they include user-controlled values in other registers. The report is eligible for a reward only if Apple can confirm that the crash submitted is plausibly exploitable in a real-world attack. To maximize the potential reward, explain how the crash demonstrates that the vulnerability might be exploited, especially if the crash looks like an unexploitable NULL-pointer dereference or assertion failure.

### Register Control
To demonstrate register control in a userland context, the report needs to include a PoV that, when run, crashes the vulnerable process, with at least one general-purpose register set to `_COMM_PAGE_ASB_TARGET_VALUE`. The register state needs to appear in the crash report of the vulnerable process, so that Apple engineers can validate the achieved control of a general-purpose register. The same applies for kernel, while using the `_COMM_PAGE_ASB_TARGET_KERN_VALUE` instead.

To qualify for the category’s maximum reward, the PoV must demonstrate full 64 bits of control. If the PoV achieves fewer than 64 but more than 32 bits of control, it is eligible for a partial reward. If the PoV can achieve fewer than 64 bits at a time and is repeatable for arbitrary addresses, make sure to include this detail in the report.

### Arbitrary Read/Write
To demonstrate arbitrary read/write capabilities, the report needs to demonstrate the ability to make the vulnerable process read from or write to `_COMM_PAGE_ASB_TARGET_ADDRESS` or `_COMM_PAGE_ASB_TARGET_KERN_ADDRESS`, based on whether targeting userspace or the kernel. To demonstrate a write, write the value from `_COMM_PAGE_ASB_TARGET_VALUE` to `_COMM_PAGE_ASB_TARGET_ADDRESS`.

Here is an example PoV that demonstrates the read/write capability in userspace: `assets/read-write-example.c`

### Arbitrary Code Execution
To demonstrate arbitrary code execution, the report needs to demonstrate the ability to make the vulnerable process jump to the address `_COMM_PAGE_ASB_TARGET_ADDRESS` or `_COMM_PAGE_ASB_TARGET_KERN_ADDRESS`. The register state needs to appear in the program’s crash report, so Apple engineers can validate the achieved control of the instruction pointer (PC register on Apple silicon).

Here is an example PoV that demonstrates the arbitrary code execution capability: `assets/code-exec-example.c`

## Transparency, Consent, and Control (TCC) Target Flag
Transparency, Consent, and Control (TCC) settings help protect sensitive user data and allow users to see which apps they granted permission to access specific information, as well as grant or revoke future access. These preferences are stored in per-user and system databases, which are read-and-write protected by Full Disk Access (FDA) and System Integrity Protection (SIP), respectively.

Easily demonstrate modifying the user or system TCC database using two new verbs added to `tccutil` — `tccutil flag check` and `tccutil flag reset`. We’ve added a table to both user and system TCC databases called `integrity_flag`. integrity_flag does not grant any permissions and has no capability except to provide a concise way to demonstrate overwriting or forging the TCC database.

After granting Full Disk Access to Terminal.app from the Security & Privacy pane under Settings.app, test this using SQLite:

```
% sqlite3 TCC.db
sqlite> select * from integrity_flag;
integrity_flag|0
sqlite> INSERT OR REPLACE INTO integrity_flag (key, value) VALUES ('integrity_flag', 1);
sqlite> select * from integrity_flag;
integrity_flag|1
% tccutil flag check
User: modified
System: default
```

`tccutil flag check` checks both the user and system TCC databases for the value of `integrity_flag`. After this inspection, `tccutil flag check` outputs “modified” for the TCC database that includes an `integrity_flag` that has been successfully modified to any value other than 0.

For convenience, `tccutil flag reset` returns `integrity_flag` to value `0`. `tccutil flag reset` does not alter any other state in the user and system TCC databases. To remove all user-level TCC selections, use `tccutil reset All`. This command does not modify the `integrity_flag`.

Here is a verbose example: `assets/tcc-verbose-example.sh`

Here is a minimal example: `assets/tcc-minimal-example.sh`

To qualify for the stated reward in this category and for accelerated awards, the report that demonstrates modifying the TCC database must use the new `tccutil` flag verbs to confirm impact. Use the above commands to check the state of the `integrity_flag` either in the PoV or in an accompanying video demonstration.
