# MaxTAC for Cloud

MaxTAC for Cloud adds AWS, Azure, and GCP vulnerability research workflows for cloud control planes, IAM, data exposure, runtime metadata, workload identity, managed Kubernetes, and cloud-specific auditor routing.

Use this pack with MaxTAC Core when the target involves cloud accounts, subscriptions, projects, organizations, service identities, storage, compute, serverless, managed Kubernetes, or cloud deployment boundaries.

## When To Use

- AWS, Azure, or GCP surface triage for authorized vulnerability research.
- Cloud IAM, RBAC, trust policy, federation, service principal, service account, or workload identity boundary analysis.
- Storage, database, snapshot, backup, key, signed URL, SAS token, or data-plane exposure research.
- Runtime, metadata service, container, serverless, managed Kubernetes, and network boundary proof.
- Cross-account, cross-tenant, cross-project, organization policy, or deployment boundary questions.

## Skills

- `maxtac-cloud-surface-triage`: initial AWS, Azure, and GCP inventory, boundary mapping, hypothesis ranking, and auditor routing.
- `maxtac-cloud-iam-boundary`: IAM, RBAC, trust, federation, service identity, and privilege-boundary proof workflows.
- `maxtac-cloud-data-exposure`: cloud storage, database, backup, snapshot, key, and signed-access exposure research.
- `maxtac-cloud-runtime-boundary`: compute, serverless, container, metadata, workload identity, managed Kubernetes, and network boundary analysis.

## Typical Pairings

- Cloud + Web when cloud control planes, SaaS consoles, OAuth/OIDC flows, APIs, SSRF, callbacks, or webhooks matter.
- Cloud + Supply Chains when CI/CD OIDC, artifact promotion, deployment roles, registries, or release-to-cloud trust paths matter.
- Cloud + Source when infrastructure-as-code, policy code, application code, or service handlers are available.
- Cloud + Binary when agents, appliances, native extensions, or cloud-hosted binaries dominate the evidence path.
- Cloud + program packs when Apple, Microsoft, Android, or other program proof rules govern cloud-delivered artifacts.

## Output Artifacts

Cloud workflows commonly produce:

- `tmp/cloud/<case-id>/` packets for surface triage, IAM boundary research, data exposure, and runtime boundary analysis.
- Resource identity maps, policy snippets, trust graphs, redacted CLI/API transcripts, audit log references, effective permission checks, and non-destructive proof steps.
- Provider-specific evidence such as AWS account/ARN/region data, Azure tenant/subscription/resource IDs, and GCP organization/folder/project/resource names.

## Boundary

This pack is for authorized vulnerability research, not broad compliance reporting. Do not report scanner output, over-permissive policy text, or public exposure alone without an affected asset, violated boundary, and reproducible proof. Pair with Web, Source, Supply Chains, or Binary when the cloud finding depends on application logic, code reachability, CI/CD trust, or native components.
