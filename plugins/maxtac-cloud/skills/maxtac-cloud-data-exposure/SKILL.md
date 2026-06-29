---
name: maxtac-cloud-data-exposure
description: "Use this skill when AWS, Azure, or GCP vulnerability research involves storage, databases, snapshots, backups, logs, keys, signed access, data-plane permissions, or cross-account data exposure."
---

# MaxTAC Cloud Data Exposure

Use this skill when the security question is whether cloud data, backups, logs, keys, or derived artifacts are exposed beyond the expected audience. Prove the data boundary and sensitivity without over-collecting data.

## Data Exposure Packet

Store results under `audits/cloud/<case-id>/data-exposure.md`:

- Provider, target scope, and resource IDs.
- Data asset: bucket, container, object prefix, database, table, snapshot, backup, image, log sink, secret, key, queue, topic, or derived artifact.
- Expected audience and access model.
- Actual access path: public, cross-account, cross-tenant, cross-project, shared link, signed URL, SAS, resource policy, ACL, inherited IAM, network bypass, backup restore, decrypt permission, or log export.
- Access type: list, read, write, delete, restore, decrypt, share, overwrite, or poison.
- Sensitivity evidence with minimal samples or metadata.
- Non-destructive proof transcript with request IDs and redactions.
- Impact, affected consumers, counterevidence, and remediation constraints.

## Workflow

1. Identify immutable resource names, object paths, region/location, encryption keys, versioning state, retention state, and public or shared endpoints.
2. Determine the intended audience from policy, docs, IaC, naming, program scope, and owner statements. Avoid assuming every public object is unintended.
3. Evaluate every data-plane path: direct object access, inherited IAM, resource policy, ACL, signed link, backup sharing, snapshot copy, replication, log sink, query service, and decrypt authority.
4. Test least privilege first: metadata/list checks, HEAD requests, dry-run or read-only calls, small harmless object reads, canary objects, and policy analyzers. Do not download bulk data.
5. Check write and overwrite paths separately from read paths. Data poisoning, log tampering, backup replacement, and key rotation can be more severe than read exposure.
6. Link exposure to affected assets and consumers. A public bucket with no sensitive or in-scope data may be informational; a signed URL to sensitive logs, backups, or secrets is materially different.

## Provider Checks

- AWS: S3 bucket and object policies, ACLs, Public Access Block, Access Points, S3 Object Lambda, EBS/RDS/Redshift snapshots, AMIs, KMS key policies and grants, Secrets Manager, SSM Parameter Store, CloudWatch logs, Athena, Glue, and Lake Formation.
- Azure: Blob containers, Data Lake Storage ACLs, SAS tokens, storage account public network access, shared keys, Key Vault access policies and RBAC, managed disks and snapshots, SQL/Cosmos backups, Monitor logs, and trusted Microsoft services bypasses.
- GCP: Cloud Storage IAM and ACLs, signed URLs, uniform bucket-level access, BigQuery datasets/tables, Cloud SQL backups, snapshots, Secret Manager versions, KMS IAM, logging sinks, and public project/resource inheritance.

## Proof Hygiene

- Capture only the minimum data needed to prove sensitivity. Prefer metadata, object names, row counts, schemas, checksums, or one redacted canary sample.
- Redact personal data, secrets, tokens, keys, and customer content in packets. Store raw sensitive evidence only when the program requires it and the workspace is approved for it.
- Record request IDs, audit log references, actor identity, timestamps, and exact resource IDs so the owner can verify the access path.

## Auditor Routing

Use Cloud auditor filters such as `data-exposure`, `storage`, `snapshot`, `kms`, `secret-manager`, `signed-url`, `network`, `aws`, `azure`, and `gcp`. Use Source when code determines object names or authorization. Use Web when the data path depends on application routes, browser state, SSRF, or signed-link generation.
