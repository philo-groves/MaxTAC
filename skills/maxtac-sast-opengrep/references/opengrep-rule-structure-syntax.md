# OpenGrep Rule Structure Syntax

OpenGrep rules are YAML objects under a top-level `rules:` list. Each rule
describes what to match, where to run, how serious the finding is, and what
message should be shown to the analyst.

## Contents

- [Minimal Rule](#minimal-rule)
- [Required Fields](#required-fields)
- [Optional Top-Level Fields](#optional-top-level-fields)
- [Core Operators](#core-operators)
- [Evaluation Order in `patterns`](#evaluation-order-in-patterns)
- [Regex Operators](#regex-operators)
- [Metavariable Filters](#metavariable-filters)
- [Context and Negative Operators](#context-and-negative-operators)
- [Metavariable Behavior](#metavariable-behavior)
- [Options](#options)
- [Paths](#paths)
- [Fixes](#fixes)
- [Metadata](#metadata)
- [Version Gates](#version-gates)
- [Complete Example](#complete-example)
- [SAST Rule-Writing Checklist](#sast-rule-writing-checklist)

## Minimal Rule

```yaml
rules:
  - id: python-flask-debug-enabled
    languages:
      - python
    severity: HIGH
    message: Flask debug mode is enabled. Disable debug mode outside local development.
    pattern: |
      $APP.run(..., debug=True, ...)
```

A rule file can contain one rule or many. Keep IDs stable because downstream
systems often use them for suppression, deduplication, and trend tracking.

## Required Fields

Each rule needs these fields:

- `id`: Stable, unique rule identifier. Prefer lowercase words separated by
  hyphens, for example `python-flask-debug-enabled`.
- `message`: Triage text explaining why the match matters and what to check or
  change.
- `severity`: Prefer `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- `languages`: One or more OpenGrep language keys, such as `python`,
  `javascript`, `typescript`, `java`, `go`, `c`, `cpp`, `csharp`, `ruby`,
  `php`, `rust`, `kotlin`, `swift`, `dockerfile`, `terraform`, `yaml`, `json`,
  `xml`, `html`, or `generic`.
- One match operator: exactly one of `pattern`, `patterns`, `pattern-either`, or
  `pattern-regex` at the rule level.

Use language aliases that your installed OpenGrep accepts. For portable rules,
prefer canonical names over short aliases unless the codebase already has a
consistent convention.

## Optional Top-Level Fields

Common optional fields:

- `paths`: Include or exclude files for this rule.
- `options`: Tune matching behavior for this rule.
- `fix`: Suggest a simple replacement for autofix workflows.
- `metadata`: Attach non-matching data such as CWE, OWASP, confidence,
  technology, references, or ownership.
- `min-version` and `max-version`: Skip rules outside a supported OpenGrep
  version range.

Condition operators such as `pattern-not`, `pattern-inside`,
`metavariable-regex`, and `metavariable-comparison` usually belong under
`patterns`, not directly at the rule top level.

## Core Operators

### `pattern`

Use `pattern` for one structural code shape.

```yaml
rules:
  - id: python-insecure-tempfile
    languages:
      - python
    severity: MEDIUM
    message: Temporary file name is generated without creating the file safely.
    pattern: |
      tempfile.mktemp(...)
```

Use this when a single expression or statement is enough to describe the issue.

### `patterns`

Use `patterns` for logical AND. Each child must apply to the same final match
range after OpenGrep combines positives, removes negatives, applies
metavariable filters, and focuses the match.

```yaml
rules:
  - id: python-subprocess-shell-user-input
    languages:
      - python
    severity: HIGH
    message: User-controlled data reaches a shell-enabled subprocess call.
    patterns:
      - pattern-inside: |
          def $FUNC(..., $REQ, ...):
              ...
      - pattern: |
          subprocess.$CALL(..., $REQ.$SOURCE, ..., shell=True, ...)
```

Use `patterns` for SAST rules that need context, exclusions, metavariable
constraints, or follow-up filtering.

### `pattern-either`

Use `pattern-either` for logical OR.

```yaml
rules:
  - id: python-weak-hash
    languages:
      - python
    severity: MEDIUM
    message: Weak hash algorithm used. Prefer a collision-resistant algorithm.
    pattern-either:
      - pattern: hashlib.md5(...)
      - pattern: hashlib.sha1(...)
```

Use this when several equivalent API calls represent the same risk.

## Evaluation Order in `patterns`

Order in the YAML list should be written for readability, but matching follows
operator classes:

1. Positive operators create candidate ranges and metavariable bindings:
   `pattern`, `pattern-inside`, `pattern-either`, nested `patterns`, and
   `pattern-regex`.
2. Negative operators remove candidates: `pattern-not`,
   `pattern-not-inside`, and `pattern-not-regex`.
3. Conditional operators filter remaining candidates:
   `metavariable-regex`, `metavariable-pattern`, and
   `metavariable-comparison`.
4. `focus-metavariable` narrows the reported range to already-bound
   metavariables.

Metavariables created only inside negative patterns are not available to later
conditional filters. Bind values in a positive pattern first.

## Regex Operators

### `pattern-regex`

Use `pattern-regex` for text-level matches. It is useful for secrets, legacy
grep migrations, and file formats where syntax-aware matching is not needed.
Regexes are evaluated in multiline mode.

```yaml
rules:
  - id: generic-private-key-header
    languages:
      - generic
    severity: CRITICAL
    message: Private key material appears in the repository.
    paths:
      exclude:
        - "testdata/**"
        - "fixtures/**"
    pattern-regex: '-----BEGIN [A-Z ]*PRIVATE KEY-----'
```

Prefer single-quoted YAML strings for regexes that contain backslashes.

Named capture groups can bind metavariables for messages or later filters. Use
uppercase group names:

```yaml
rules:
  - id: generic-url-with-credentials
    languages:
      - generic
    severity: HIGH
    message: URL contains credentials for host $HOST.
    pattern-regex: 'https?://[^/\s:@]+:[^/\s:@]+@(?P<HOST>[^/\s]+)'
```

### `pattern-not-regex`

Use `pattern-not-regex` to remove text matches that overlap a regex.

```yaml
rules:
  - id: generic-hardcoded-token
    languages:
      - generic
    severity: HIGH
    message: Hardcoded token-like value found outside examples.
    patterns:
      - pattern-regex: '\btoken_[A-Za-z0-9]{24,}\b'
      - pattern-not-regex: 'example|placeholder|dummy'
```

This is often clearer than a large negative lookahead.

## Metavariable Filters

### `focus-metavariable`

Use `focus-metavariable` to report only the code bound to an existing
metavariable. It does not create a match by itself.

```yaml
rules:
  - id: python-dangerous-default-argument
    languages:
      - python
    severity: MEDIUM
    message: Mutable default argument can leak state between calls.
    patterns:
      - pattern: |
          def $FUNC(..., $ARG={}, ...):
              ...
      - focus-metavariable: $ARG
```

`focus-metavariable: $ARG` is different from `pattern: $ARG`. The former
narrows the existing finding; the latter searches the code for expressions
matching `$ARG`.

When a list is supplied, OpenGrep reports the intersection of the focused
ranges:

```yaml
patterns:
  - pattern: dangerous($A, ..., $B)
  - focus-metavariable:
      - $A
      - $B
```

Use focus sparingly. It is most useful when the full match is a large function,
class, object literal, or block but the triage-relevant region is small.

### `metavariable-regex`

Use `metavariable-regex` to filter by the text bound to a metavariable. Matching
is left anchored, so add `.*` when the interesting text may occur after a
prefix.

```yaml
rules:
  - id: python-risky-request-header
    languages:
      - python
    severity: MEDIUM
    message: Request header $HEADER is forwarded from user-controlled input.
    patterns:
      - pattern: |
          headers[$HEADER] = request.$SOURCE(...)
      - metavariable-regex:
          metavariable: $HEADER
          regex: '.*(Authorization|Cookie|X-Api-Key).*'
```

When filtering a string literal, remember that the captured value may include
quotes. Test both quoted and unquoted expectations.

### `metavariable-pattern`

Use `metavariable-pattern` to run a structural formula against the code captured
by a metavariable. It requires `metavariable` plus one formula key: `pattern`,
`patterns`, `pattern-either`, or `pattern-regex`.

```yaml
rules:
  - id: javascript-express-open-redirect
    languages:
      - javascript
    severity: HIGH
    message: Redirect target includes request-controlled data.
    patterns:
      - pattern: |
          $RES.redirect($TARGET)
      - metavariable-pattern:
          metavariable: $TARGET
          pattern-either:
            - pattern: $REQ.query.$KEY
            - pattern: $REQ.body.$KEY
            - pattern: $REQ.params.$KEY
```

`metavariable-pattern` can be nested when a capture must be decomposed further.
It works best when the metavariable is an expression, statement, or statement
list. It is not a good fit for captures that are only argument lists, types, or
patterns.

Use `language` to inspect captured text as another language. This is helpful for
strings, templates, HTML script blocks, SQL fragments, or generic config
snippets.

```yaml
rules:
  - id: html-inline-script-document-write
    languages:
      - generic
    severity: MEDIUM
    message: Inline script calls document.write.
    patterns:
      - pattern: |
          <script ...>$...JS</script>
      - metavariable-pattern:
          metavariable: $...JS
          language: javascript
          pattern: |
            document.write(...)
```

### `metavariable-comparison`

Use `metavariable-comparison` for numeric, string, date, or simple boolean
conditions over metavariable values.

```yaml
rules:
  - id: python-privileged-port-binding
    languages:
      - python
    severity: MEDIUM
    message: Application binds to a privileged port; verify this is intentional.
    patterns:
      - pattern: |
          $APP.run(..., port=$PORT, ...)
      - metavariable-comparison:
          metavariable: $PORT
          comparison: $PORT < 1024
```

Useful comparison tools include boolean operators, arithmetic, comparisons,
`int()`, `str()`, string containment with `in`, list membership with `in`,
`re.match()`, `lower()`, `upper()`, `today()`, and `strptime()`.

If a metavariable binds to a literal or propagated constant, comparisons use
that value. Otherwise, use `str($MVAR)` to compare against the source text.

Prefer explicit conversion with `int()` over legacy conversion keys.

## Context and Negative Operators

### `pattern-not`

Use `pattern-not` to remove exact safe variants from a positive match.

```yaml
rules:
  - id: python-requests-disable-tls-verify
    languages:
      - python
    severity: HIGH
    message: TLS certificate verification is disabled.
    patterns:
      - pattern: |
          requests.$METHOD(..., verify=$VERIFY, ...)
      - metavariable-comparison:
          metavariable: $VERIFY
          comparison: $VERIFY == False
      - pattern-not: |
          requests.$METHOD(..., verify=False, timeout=1, ...)
```

`pattern-not` can also negate a nested `patterns` or `pattern-either` formula:

```yaml
patterns:
  - pattern: db.query($SQL)
  - pattern-not:
      pattern-either:
        - pattern: db.query($SQL, safe=True)
        - pattern: safe_query($SQL)
```

### `pattern-inside`

Use `pattern-inside` to keep findings inside a required context.

```yaml
rules:
  - id: python-debug-route-returns-env
    languages:
      - python
    severity: HIGH
    message: Flask route returns process environment data.
    patterns:
      - pattern-inside: |
          @$APP.route(...)
          def $HANDLER(...):
              ...
      - pattern: |
          return os.environ
```

Multiple `pattern-inside` clauses narrow the context further.

### `pattern-not-inside`

Use `pattern-not-inside` to exclude mitigated, test-only, or controlled
contexts.

```yaml
rules:
  - id: python-open-without-context-manager
    languages:
      - python
    severity: LOW
    message: File is opened outside a context manager; verify it is closed.
    patterns:
      - pattern: |
          $F = open(...)
      - pattern-not-inside: |
          with open(...) as $F:
              ...
```

For missing-cleanup checks, bind the resource in the positive pattern and use
the same metavariable in the negative context:

```yaml
patterns:
  - pattern: |
      $LOCK.acquire()
  - pattern-not-inside: |
      $LOCK.acquire()
      ...
      $LOCK.release()
```

## Metavariable Behavior

In `patterns`, repeated metavariable names must bind to the same code across
the ANDed formula:

```yaml
patterns:
  - pattern-inside: |
      def $FUNC($ARG):
          ...
  - pattern: |
      open($ARG)
```

This matches only when the function argument itself is passed to `open`.

Inside `pattern-either`, metavariable names do not force equality across
different OR branches. They bind independently in whichever branch matches:

```yaml
pattern-either:
  - pattern: insecure_load($VALUE)
  - pattern: unsafe_parse($VALUE)
```

If a `pattern-either` appears inside a parent `patterns` list, metavariables
bound by earlier positive patterns can still constrain the OR branches:

```yaml
patterns:
  - pattern-inside: |
      def $FUNC($INPUT):
          ...
  - pattern-either:
      - pattern: execute($INPUT)
      - pattern: render_template_string($INPUT)
```

Use this behavior to express "same source, one of several sinks" cleanly.

## Options

Use `options:` to tune matching for a single rule.

Common options:

- `ac_matching`: Treat supported associative or commutative operators as
  equivalent. Enabled by default in many builds.
- `attr_expr`: Allow expression patterns to match annotations or attributes.
- `commutative_boolop`: Treat boolean AND and OR as commutative. This can help
  search, but may not be semantically exact.
- `constant_propagation`: Let literal constants match through variables.
- `decorators_order_matters`: Make Python decorator order significant.
- `generic_comment_style`: In generic mode, ignore comments with `c`, `cpp`, or
  `shell` syntax.
- `generic_ellipsis_max_span`: In generic mode, set how many newlines `...` can
  span. Use `0` for line-oriented formats.
- `implicit_return`: Let return patterns match final expressions in languages
  with implicit returns.
- `interfile`: Enable cross-function or cross-file analysis when supported by
  the installed OpenGrep engine.
- `symmetric_eq`: Treat `a == b` and `b == a` as equivalent.
- `taint_assume_safe_functions`: In taint rules, assume function calls do not
  propagate taint from arguments to return values unless modeled.
- `taint_assume_safe_indexes`: In taint rules, avoid treating indexed access as
  tainted only because the index is tainted.
- `taint_unify_mvars`: In taint rules, require source and sink metavariables
  with the same name to refer to the same code.
- `vardef_assign`: Let assignment patterns match variable declarations.
- `xml_attrs_implicit_ellipsis`: Let XML, JSX, and HTML element patterns omit
  attributes.

Options can materially change false positives and false negatives. Document
non-default options in rule metadata or comments near the rule.

## Paths

Use `paths:` to scope rules to relevant files.

```yaml
paths:
  include:
    - "apps/api/**/*.py"
    - "services/**/handlers/*.py"
  exclude:
    - "**/*_test.py"
    - "**/fixtures/**"
```

Path patterns are evaluated relative to the scan root. When include and exclude
both match, exclude wins. Add rule test files to included paths when path
filters would otherwise skip them.

Use path filters aggressively for generic, regex, framework-specific, and
configuration-file rules.

## Fixes

Use `fix:` for simple textual replacements. Fixes can include metavariables
bound by the match.

```yaml
rules:
  - id: python-yaml-load-without-safe-loader
    languages:
      - python
    severity: HIGH
    message: yaml.load without SafeLoader can deserialize unsafe objects.
    pattern: |
      yaml.load($DATA)
    fix: |
      yaml.safe_load($DATA)
```

Only add fixes when they are mechanically safe. For security rules, a fix should
not silently change behavior in ways that need architectural review.

## Metadata

Use `metadata:` for data that helps triage, reporting, and rule maintenance.
Metadata does not affect matching unless another tool in the workflow consumes
it.

```yaml
metadata:
  category: security
  cwe:
    - "CWE-502"
  owasp:
    - "A08:2021"
  confidence: HIGH
  likelihood: MEDIUM
  impact: HIGH
  technology:
    - python
    - pyyaml
  references:
    - "https://pyyaml.org/wiki/PyYAMLDocumentation"
```

Keep metadata keys consistent across the ruleset. Prefer structured lists for
fields that may have multiple values.

## Version Gates

Use `min-version` and `max-version` when a rule relies on engine behavior that
older or newer OpenGrep versions may not support.

```yaml
rules:
  - id: javascript-newer-parser-feature
    min-version: 1.20.0
    languages:
      - javascript
    severity: MEDIUM
    message: Pattern relies on parser support added in newer OpenGrep releases.
    pattern: |
      using $RESOURCE = $EXPR
```

Version gates are most useful for shared rule packs that run across many
developer machines or CI images.

## Complete Example

This rule finds Python open redirects where a redirect target is derived from
request data, while allowing a known-safe helper.

```yaml
rules:
  - id: python-flask-open-redirect
    languages:
      - python
    severity: HIGH
    message: Redirect target is derived from request data. Validate or restrict the destination.
    metadata:
      category: security
      cwe:
        - "CWE-601"
      technology:
        - flask
      confidence: HIGH
    paths:
      include:
        - "**/*.py"
      exclude:
        - "**/tests/**"
        - "**/fixtures/**"
    patterns:
      - pattern-inside: |
          @$APP.route(...)
          def $HANDLER(...):
              ...
      - pattern: |
          redirect($TARGET)
      - metavariable-pattern:
          metavariable: $TARGET
          pattern-either:
            - pattern: request.args.get(...)
            - pattern: request.form.get(...)
            - pattern: request.values.get(...)
      - pattern-not: |
          redirect(safe_redirect_target($TARGET))
      - focus-metavariable: $TARGET
```

Why it is structured this way:

- `pattern-inside` limits the rule to route handlers.
- `pattern` identifies the sink.
- `metavariable-pattern` requires request-controlled data.
- `pattern-not` removes a project-specific sanitizer.
- `focus-metavariable` reports the risky redirect target, not the whole route.

## SAST Rule-Writing Checklist

- Start with a precise sink or risky API call.
- Add context with `pattern-inside` only when it improves signal.
- Bind source, sink, sanitizer, and receiver names with metavariables.
- Use `pattern-either` for equivalent APIs or framework variants.
- Use `pattern-not` and `pattern-not-inside` for known-safe wrappers, tests, and
  framework helpers.
- Use `metavariable-pattern` when a captured expression needs structural
  inspection.
- Use `metavariable-regex` for naming conventions, literal values, and captured
  text filters.
- Use `metavariable-comparison` for numeric thresholds, modes, ports, dates, and
  constant values.
- Keep regex rules path-scoped and explain why structural matching is not used.
- Put high-signal triage details in `message` and stable taxonomy in
  `metadata`.
- Test positive and negative snippets before adding a rule to a shared pack.
