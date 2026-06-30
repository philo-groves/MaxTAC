---
name: maxtac-cloud-surface-triage
description: "Use this skill when AWS, Azure, or GCP vulnerability research needs initial account, subscription, project, service, identity, data, runtime, network, or trust-boundary triage."
---

# MaxTAC Cloud Surface Triage

Use this skill as the first pass for authorized AWS, Azure, and GCP vulnerability research. The goal is a compact map of cloud actors, resources, identities, data assets, runtime boundaries, network paths, audit sources, and high-value hypotheses that can be handed to Cloud auditors or deeper domain packs.

## Operating Rules

- Start from the authorized scope: cloud provider, organization/account/subscription/project, region, service family, tenant boundary, and allowed proof actions.
- Record durable identifiers: AWS account IDs, ARNs, regions, role session names, CloudTrail event IDs; Azure tenant IDs, subscription IDs, resource IDs, object IDs, correlation IDs; GCP organization/folder/project IDs, resource names, service accounts, audit log insert IDs.
- Separate control-plane authority, data-plane access, runtime identity, and network reachability. A finding is stronger when it crosses a named boundary.
- Prefer provider-native evidence, infrastructure-as-code, policy JSON, audit logs, and redacted CLI/API transcripts over console screenshots alone.
- Do not print or store live secrets, bearer tokens, session credentials, or private keys. Capture redacted claims, key IDs, role names, scopes, and timestamps.
- Use `maxtac-cloud-iam-boundary` for IAM, RBAC, federation, impersonation, and delegated authority questions.
- Use `maxtac-cloud-data-exposure` for storage, database, snapshot, backup, signed access, and key/data-plane exposure questions.
- Use `maxtac-cloud-runtime-boundary` for compute, serverless, container, metadata service, managed Kubernetes, workload identity, and network boundary questions.
- Pair with Supply Chains when CI/CD OIDC, artifact promotion, registry, signing, or deployment authority is the root boundary.
- Pair with Web when SSRF, OAuth/OIDC, cloud consoles, SaaS workflows, webhooks, callbacks, or browser state are part of the proof.

## Triage Workflow

1. Define the target slice: provider, environment, account/subscription/project, region, service family, asset class, and program-approved proof limits.
2. Inventory identities and boundaries: humans, roles, service principals, managed identities, service accounts, workload identities, groups, permission boundaries, deny policies, organization policies, tenant/project/account inheritance, and federation paths.
3. Inventory protected assets: storage buckets, blobs, databases, snapshots, secrets, KMS keys, logs, queues, registries, workloads, clusters, functions, APIs, private endpoints, and management-plane resources.
4. Map runtime surfaces: VMs, serverless functions, jobs, containers, managed Kubernetes, metadata services, execution roles, node identities, secret mounts, and egress paths.
5. Map control evidence: AWS CloudTrail/Config/Access Analyzer/GuardDuty, Azure Activity Logs/Entra audit logs/Azure Policy/Defender, GCP Cloud Audit Logs/Policy Analyzer/Security Command Center, and relevant IaC.
6. Rank hypotheses by boundary crossed, affected asset sensitivity, reproducibility, least-privilege delta, auditability, and proof safety.
7. Route to the narrowest Cloud skill and auditor filter before expanding to Web, Source, Supply Chains, or Binary.

## Cloud Surface Triage Packet

When a file packet is useful, store results under `tmp/cloud/<case-id>/surface-triage.md`:

```markdown
## Cloud Surface Triage Packet

- Provider and target slice:
- Authorized scope and proof limits:
- Account/subscription/project/tenant/resource IDs:
- Region(s):
- Actor and starting credential:
- Target asset or trust boundary:
- Control-plane authority:
- Data-plane access:
- Runtime/workload identity:
- Network/perimeter state:
- Federation or delegation path:
- Relevant policies and deny controls:
- Audit/log sources:
- Controlled inputs:
- Security invariant:
- Suspect crossing or policy gap:
- Non-destructive proof plan:
- Evidence collected:
- Evidence still needed:
- Suggested skill: IAM Boundary / Data Exposure / Runtime Boundary / Web / Source / Supply Chains / Binary
- Suggested auditor filters:
- Candidate hypothesis:
- Confidence: low / medium / high
```

## Provider Pivots

- AWS: account ID, organization/SCPs, IAM policies, resource policies, trust policies, STS sessions, permission boundaries, VPC endpoints, CloudTrail, Access Analyzer, Config, and service-linked roles.
- Azure: tenant, management group, subscription, resource group, RBAC assignments, custom roles, Entra applications, service principals, managed identities, Key Vault, private endpoints, Activity Logs, and Defender/Policy state.
- GCP: organization, folders, projects, IAM bindings, service accounts, workload identity federation, organization policy, VPC Service Controls, Cloud Audit Logs, Policy Analyzer, and Security Command Center.

## Auditor Routing

Use the Cloud pack's auditor MCP tools when available. If those tools are not exposed in the current context, use Core's local fallback: `python3 <maxtac-core-subagents-skill-dir>/scripts/audit-helper.py --catalog cloud --filter <term>`. Good starting filters include `iam`, `rbac`, `federation`, `data-exposure`, `storage`, `snapshot`, `runtime`, `metadata`, `serverless`, `kubernetes`, `network`, `secrets`, `kms`, `aws`, `azure`, and `gcp`.
