---
name: maxtac-cloud-iam-boundary
description: "Use this skill when AWS, Azure, or GCP vulnerability research depends on IAM, RBAC, trust policy, federation, service identity, impersonation, delegated deployment authority, or privilege-boundary proof."
---

# MaxTAC Cloud IAM Boundary

Use this skill when the security question is whether a cloud principal can obtain, delegate, impersonate, or exercise authority beyond the intended boundary. Focus on proving the boundary crossing, not merely finding broad permissions.

## IAM Boundary Packet

When a file packet is useful, store results under `tmp/cloud/<case-id>/iam-boundary.md`:

- Provider and target scope.
- Starting principal: user, role, service principal, managed identity, service account, workload identity, federated subject, CI/CD identity, or runtime identity.
- Target boundary: account, tenant, subscription, project, folder, organization, resource group, namespace, environment, role, data asset, or deployment authority.
- Policy sources: identity policies, resource policies, trust policies, permission boundaries, SCPs, deny assignments, Azure RBAC/custom roles, Entra app permissions, GCP IAM bindings, organization policies, conditions, and inherited grants.
- Escalation or delegation path: assume, impersonate, act-as, pass-role, assign-role, attach-policy, create-token, deploy-as, write-workflow, create-function, modify-trigger, or grant-access.
- Deny controls and compensating controls.
- Non-destructive proof transcript with secrets redacted.
- Impact, affected assets, audit trail, counterevidence, and remaining proof gaps.

## Workflow

1. Normalize identities and scopes. Record stable IDs, role names, object IDs, service account emails, account/subscription/project IDs, regions, and timestamped CLI/API context.
2. Build the effective permission set from both allows and denies. Include inherited organization controls and resource policies before calling a path exploitable.
3. Trace trust edges, not just permissions. Identify who can mint or receive credentials, who can pass or bind roles, who can update policies, and who can deploy code that runs as another identity.
4. Check condition keys and context: external ID, audience, subject, issuer, source ARN/account, principal tags, session tags, resource tags, MFA, device state, IP, network, time, and workload attributes.
5. Prove with the least invasive action. Prefer policy simulation, access-analyzer output, read-only calls, dry-run APIs, or a program-approved test resource. Do not create persistent admin access unless explicitly authorized.
6. Link IAM authority to impact. A high-privilege policy is not a finding unless the starting actor can reach it and it affects in-scope assets.

## Provider Checks

- AWS: `sts:AssumeRole`, `iam:PassRole`, role trust policies, resource policies, permission boundaries, SCPs, session policies, `CreatePolicyVersion`, `Attach*Policy`, `UpdateAssumeRolePolicy`, Lambda/ECS/EC2 role use, CloudFormation/CDK deployment roles, EventBridge/Scheduler targets, and OIDC trust for CI.
- Azure: role assignments, custom role `actions` and `dataActions`, management group inheritance, deny assignments, Entra application ownership, app roles, Graph permissions, service principal credentials, managed identities, PIM, deployment scripts, automation accounts, and Azure DevOps/GitHub federation.
- GCP: `iam.serviceAccounts.actAs`, Service Account Token Creator, `setIamPolicy`, folder/project inheritance, custom roles, workload identity federation, Cloud Build service accounts, deployment manager or Terraform identities, Cloud Run/Functions execution identities, and organization policy exceptions.

## Proof Hygiene

- Redact access keys, tokens, JWT signatures, refresh tokens, private keys, SAS tokens, and service principal secrets.
- Capture claims and metadata needed for verification: issuer, subject, audience, tenant/account/project, role ARN or object ID, scopes, policy IDs, token lifetime, request ID, and audit log reference.
- Avoid changing production policy. If mutation is required, use a throwaway resource inside the authorized environment and record cleanup.

## Auditor Routing

Use Cloud auditor filters such as `iam`, `rbac`, `federation`, `privilege-escalation`, `aws`, `azure`, `gcp`, `workload-identity`, and `secrets`. Use Supply Chains when the identity comes from CI/CD OIDC or release automation, and use Web when OAuth/OIDC web flows or SSRF are required to obtain the starting credential.
