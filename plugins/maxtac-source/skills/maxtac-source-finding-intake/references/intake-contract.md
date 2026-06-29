# MaxTAC Intake Contract

`maxtac.intake/v1` preserves external finding claims without forcing them into a completed MaxTAC finding or report schema.

```json
{
  "document_type": "maxtac.intake",
  "schema_version": "maxtac.intake/v1",
  "intake_id": "intake-20260628",
  "repository": {
    "path": "/path/to/repo",
    "revision": "optional git revision"
  },
  "items": []
}
```

Each item uses:

```json
{
  "intake_item_id": "intake-0001",
  "input_id": "external id or empty",
  "source_type": "sarif",
  "title": "claim title",
  "normalized_input": {
    "vulnerable_component": "package, file, API, route, function, service, or unknown",
    "claimed_source": "attacker-controlled input or unknown",
    "claimed_sink": "sink or broken control or unknown",
    "claimed_control": "missing guard, sanitizer, auth check, or unknown",
    "affected_version_or_path": "affected version, path, config, or unknown",
    "preconditions": [],
    "impact": "claimed impact or unknown",
    "references": []
  },
  "triage": {
    "verdict": "needs_review",
    "confidence": "low",
    "affected_locations": [],
    "reachable_path": [],
    "boundary_assessment": {
      "product_surface": "unknown",
      "source_trust": "unknown",
      "boundary_crossed": null,
      "policy_basis": "unknown"
    },
    "exploitability_rank": {
      "rank_queue": null,
      "rank": null,
      "rationale": "",
      "drivers": []
    },
    "evidence": [],
    "counterevidence": [],
    "proof_gaps": [],
    "recommended_next_step": "",
    "handoff": ""
  }
}
```

Allowed `source_type` values are `sarif`, `github_code_scanning`, `dependabot`, `cve`, `ghsa`, `advisory`, `scanner_ticket`, `bug_bounty`, `jira`, `linear`, `freeform`, `json`, and `unknown`.

Allowed verdicts are `confirmed`, `not_actionable`, and `needs_review`.
