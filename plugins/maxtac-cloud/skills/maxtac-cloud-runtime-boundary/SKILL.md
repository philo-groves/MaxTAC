---
name: maxtac-cloud-runtime-boundary
description: "Use this skill when AWS, Azure, or GCP vulnerability research involves compute, serverless, containers, metadata services, workload identity, managed Kubernetes, network perimeters, or runtime-to-cloud privilege paths."
---

# MaxTAC Cloud Runtime Boundary

Use this skill when code execution, request influence, container control, pod control, SSRF, or runtime configuration may cross a cloud identity, metadata, network, or workload boundary.

## Runtime Boundary Packet

Store results under `audits/cloud/<case-id>/runtime-boundary.md`:

- Provider, target service, runtime, region, and resource IDs.
- Starting capability: HTTP request influence, SSRF, container shell, pod exec, job control, function update, environment read, build step, or VM access.
- Runtime identity: instance profile, execution role, task role, managed identity, service account, workload identity, node identity, or deployment identity.
- Metadata and credential boundary: endpoint, token requirement, hop limit, audience, projected token, network path, headers, and redacted claims.
- Network boundary: ingress, egress, security group/NSG/firewall, VPC/VNet, private endpoint, service perimeter, NAT/proxy, and DNS state.
- Reached resource or denied control.
- Non-destructive proof transcript with secrets redacted.
- Impact, affected assets, counterevidence, safety controls, and remaining proof gaps.

## Workflow

1. Define the starting capability and runtime. Distinguish request influence, application SSRF, code execution, container escape, pod control, function deployment, CI job control, and VM access.
2. Identify the runtime identity and credential source. Record stable IDs, role/service account names, token audience, expiry, policy attachments, and audit log references without storing raw secrets.
3. Map metadata access and defenses. Check required headers, session tokens, hop limits, metadata concealment, network policies, IMDS endpoint settings, and workload identity projection.
4. Map network reachability. Include private endpoints, VPC/VNet routes, service perimeters, firewall rules, DNS, egress proxies, load balancers, NAT, and management API access.
5. Test the weakest non-destructive proof. Prefer token metadata, caller identity, policy simulation, denied calls, read-only resource listings, canary resources, or safe self-introspection.
6. Connect the runtime crossing to impact. A reachable metadata endpoint matters when the resulting identity can access in-scope assets or materially weakens isolation.

## Provider Checks

- AWS: EC2 IMDSv2 and hop limit, ECS task metadata and task roles, EKS IRSA and Pod Identity, Lambda execution roles, instance profiles, SSM, security groups, VPC endpoints, PrivateLink, service-linked roles, and CloudTrail events.
- Azure: IMDS, managed identities, App Service and Functions identities, Container Apps and ACI identities, AKS Workload Identity, node managed identities, NSGs, private endpoints, service endpoints, deployment slots, and Activity Log/Entra evidence.
- GCP: metadata service with `Metadata-Flavor`, service account scopes, Cloud Run and Cloud Functions service identities, GKE Workload Identity, node service accounts, VPC Service Controls, firewall rules, serverless VPC connectors, and Cloud Audit Logs.

## Managed Kubernetes Checks

- Inventory namespace, service account, RBAC verbs, projected tokens, automount state, pod security context, host access, secret mounts, image pull secrets, admission webhooks, network policy, and node identity.
- For EKS, validate OIDC trust policy subject/audience conditions, IRSA/Pod Identity bindings, and node role fallback.
- For AKS, validate federated identity credentials, managed identity assignment, Azure RBAC, and legacy AAD Pod Identity behavior.
- For GKE, validate Kubernetes service account to Google service account bindings, node scopes, metadata concealment, Workload Identity mode, and VPC Service Controls.

## Proof Hygiene

- Do not store raw cloud credentials, JWT signatures, access tokens, refresh tokens, client secrets, private keys, or metadata session tokens.
- Redact token bodies unless claims are needed; if claims are needed, keep issuer, subject, audience, expiry, principal ID, and role/service account only.
- Avoid destructive runtime actions. Use owned canary resources or read-only calls when proving permission.

## Auditor Routing

Use Cloud auditor filters such as `runtime`, `metadata`, `serverless`, `container`, `kubernetes`, `workload-identity`, `network`, `secrets`, `aws`, `azure`, and `gcp`. Use Web when SSRF or request routing is the entrypoint, Supply Chains when CI/CD creates the runtime identity, and Binary when an agent, extension, or native component is the boundary.
