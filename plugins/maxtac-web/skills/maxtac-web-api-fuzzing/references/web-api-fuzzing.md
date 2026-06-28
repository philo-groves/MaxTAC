# Web and API Fuzzing

Use this reference for REST, GraphQL, web request, parameter, route, and
template-driven HTTP fuzzing.

Web/API fuzzing is mostly an oracle and state-model problem. The fuzzer must
know enough about authentication, CSRF, resource creation, tenant separation,
and cleanup to avoid generating only rejected or impossible requests.

## Tool Selection

Use RESTler when:

- An OpenAPI specification exists or can be produced from traffic and code.
- Bugs require request sequences, producer-consumer dependencies, or resource
  lifecycles.
- The service is stateful and single-request fuzzing only finds shallow 4xx/5xx
  noise.

Use Schemathesis when:

- OpenAPI or GraphQL schemas are available.
- Fast local or CI fuzzing is needed.
- Minimal `curl` reproducers and pytest-style integration are useful.
- The goal is to find schema violations, server errors, auth inconsistencies,
  and unexpected behavior quickly.

Use Nuclei when:

- Captured HTTP traffic or crawled endpoints should be fuzzed repeatedly with
  versioned templates.
- The target class maps to reusable vulnerability patterns such as SQLi, XSS,
  SSRF, path traversal, command injection, open redirect, template injection,
  cache poisoning, or auth bypass probes.
- Preconditions can keep a template from running against irrelevant requests.

Use Burp Intruder when:

- The work needs human-guided payload positions, session handling, CSRF repair,
  request comparison, grep/extract behavior, and quick manual iteration.

Use ZAP Fuzzer when:

- An open-source GUI workflow is preferred.
- Payload processors, scripts, or ZAP history are already part of the workflow.

Use ffuf when:

- The goal is route, vhost, directory, file, parameter, header, or value
  discovery.
- A fast baseline/filtering loop is needed before deeper proofing.

## State Model First

Before fuzzing an API, identify:

- Authentication mechanism and token refresh behavior.
- Tenant, user, project, workspace, organization, or account boundary.
- Resource creation operations and their returned identifiers.
- Resource cleanup operations and quota limits.
- Idempotent operations that can be safely fuzzed for longer.
- Dangerous operations that need a local test target, mock tenant, or explicit
  permission.
- Rate limits, replay protections, anti-CSRF rules, and request signing.

For each endpoint, decide whether fuzzing should target:

- Parameter value mutation.
- Header mutation.
- Body field mutation.
- Missing, duplicated, null, nested, overlong, or type-confused fields.
- Sequence ordering.
- Cross-user or cross-tenant object references.
- Pagination, filtering, sorting, cursor, and projection logic.
- File upload metadata and content.
- Webhook callback URLs and SSRF-style fetch behavior.

## Oracles Beyond Status Codes

Do not treat all 500s as vulnerabilities or all 200s as safe. Useful API
oracles include:

- Authenticated user can read, modify, delete, or infer another subject's data.
- Server error reveals stack traces, paths, secrets, object IDs, or internal
  service names.
- Invalid state transition succeeds.
- Resource ownership changes unexpectedly.
- A supposedly read-only request mutates state.
- A malformed request causes durable corruption, stuck jobs, lock contention,
  quota exhaustion, or background retries.
- Response body violates the schema in a security-relevant way.
- Latency or side effects reveal existence of private resources.
- Idempotency keys, replay protections, or request signatures can be bypassed.
- Cleanup fails and leaves privileged or cross-tenant artifacts.

Pair automated findings with manual replay under the debugger/browser tooling
when possible.

## RESTler Notes

RESTler is strongest when the OpenAPI spec describes enough request and response
shape for dependency inference. Improve results by adding:

- Auth configuration that matches real user roles.
- Custom dictionaries for object names, enum values, boundary values, and known
  interesting strings.
- Annotations or examples for IDs that are returned by producer requests.
- Checkers relevant to the security boundary under test.
- Cleanup and rate-limit settings for long campaigns.

Preserve the compiled grammar, settings file, dictionaries, request sequences,
bug buckets, and replay commands.

## Schemathesis Notes

Schemathesis is useful early because it turns schemas into generated tests
quickly and can adapt from server responses. For vulnerability research:

- Run it once against a fresh disposable environment before tuning.
- Separate schema-quality bugs from security bugs.
- Keep generated curl reproducers and HAR/JUnit output when available.
- Add custom checks for auth boundaries, sensitive fields, and expected
  invariants.
- Use stateful behavior when operation chaining is needed.

## Nuclei Notes

Nuclei fuzzing works best when templates are target-aware:

- Use preconditions so templates only run on relevant methods, content types,
  request bodies, or parameter shapes.
- Keep matchers strict enough to avoid reflected-payload false positives.
- Use extractors to capture tokens, object IDs, headers, and dynamic values.
- Version custom templates with the proof.
- Treat community templates as leads until manually replayed and scoped.

Nuclei is not a replacement for a stateful API fuzzer when request order and
resource lifecycles are the hard part.

## Burp, ZAP, and ffuf Notes

For Burp Intruder and ZAP Fuzzer:

- Start from a real request captured after the user flow reaches the target
  state.
- Mark only the payload positions that cross the suspected boundary.
- Keep cookies, CSRF tokens, and request signatures valid or intentionally
  mutate them as a separate experiment.
- Use grep/match/extract rules for stack traces, canaries, object IDs, and
  invariant breaks.
- Save the full request/response pairs for proof.

For ffuf:

- Always baseline false positives with control words and known-missing values.
- Filter on size, word count, line count, status, redirect location, and timing.
- Re-run hits through a browser or proxy with the real session state.

## Evidence Checklist

Collect:

- Scope, target environment, user roles, tenant IDs, rate limits, and cleanup
  constraints.
- API spec, GraphQL schema, captured traffic, HAR, Postman/Insomnia collections,
  and auth setup.
- Tool versions, commands, config files, templates, dictionaries, and generated
  state model.
- Request sequence, response bodies, headers, cookies, object IDs, timing, and
  cleanup actions.
- Minimal replay as curl, HAR, RESTler replay, Schemathesis output, Burp item,
  ZAP message, or Nuclei template.
- Proof that the behavior is security-relevant and not only schema drift or a
  benign validation error.

## References

- https://github.com/microsoft/restler-fuzzer
- https://www.microsoft.com/en-us/research/publication/restler-stateful-rest-api-fuzzing/
- https://schemathesis.readthedocs.io/
- https://github.com/schemathesis/schemathesis
- https://docs.projectdiscovery.io/templates/protocols/http/fuzzing-overview
- https://github.com/projectdiscovery/nuclei
- https://github.com/projectdiscovery/nuclei-templates
- https://portswigger.net/burp/documentation/desktop/tools/intruder/uses/fuzzing
- https://portswigger.net/burp/documentation/desktop/tools/intruder/getting-started
- https://www.zaproxy.org/docs/desktop/addons/fuzzer/
- https://www.zaproxy.org/docs/desktop/addons/fuzzer/dialogue/
- https://github.com/ffuf/ffuf
- https://arxiv.org/html/2603.28452
