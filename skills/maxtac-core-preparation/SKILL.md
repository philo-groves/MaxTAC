---
name: maxtac-core-preparation
description: Preparation phase instructions, with a different approach depending on the type of vulnerability research target.
---

# MaxTAC Core Preparation
Use this skill when recon or threat analysis should be performed on a target. A thorough preparation sets the foundation for successful research.

## Per-Target Setup
Recon and threat modeling approached depend on the category of target being researched: source code or binary.

### Source Code Preparation
Source code targets have most rich set of recon materials. For source code preparation guidance, read `assets/source-code-preparation.md`

### Binary Preparation
Binary targets are more difficult to recon than source code, but not impossible. For binary preparation guidance, read `assets/binary-preparation.md`

### STRIDE Modeling
No matter the category of preparation, STRIDE threat modeling is recommended: a developer-focused model to identify and classify threats under 6 types of attacks – Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service DoS, and elevation of privilege.

- Spoofing Identity: Attackers impersonate legitimate users, devices, or systems to bypass authentication mechanisms and gain unauthorized access.
- Tampering with Data: Attackers modify data, code, or system components without authorization to alter system behavior or compromise data integrity.
- Repudiation: Users or attackers deny performing specific actions, making it difficult to prove accountability or trace malicious activities.
- Information Disclosure: Attackers gain unauthorized access to confidential data through system vulnerabilities, misconfigurations, or weak access controls.
- Denial of Service (DoS): Attackers disrupt system availability by consuming resources, exploiting vulnerabilities, or overwhelming services to prevent legitimate access.
- Elevation of Privilege: Attackers exploit system weaknesses to gain higher privileges than intended, accessing restricted resources or administrative functions.

#### STRIDE Step 1: Decompose
- Break the system into smaller modules or services.
- Identify all entry points where data enters the system.
- Map data flows to understand how information moves logically.

#### STRIDE Step 2: Categorize
- Apply the STRIDE mnemonic to each system component.
- Check for Spoofing, Tampering, Repudiation, and Information Disclosure.
- Evaluate risks of Denial of Service and Elevation of Privilege.

#### STRIDE Step 3: Mitigate
- Prioritize threats based on their potential business impact.