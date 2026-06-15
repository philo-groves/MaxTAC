# OpenGrep Taint Analysis

Use taint rules when a finding depends on data flow from an untrusted source to
a security-sensitive sink. Taint mode is the right tool for injection,
open-redirect, path traversal, unsafe deserialization, insecure logging, and
similar bugs where a simple pattern cannot prove that attacker-controlled data
reaches the risky operation.

## Contents

- [Minimal Taint Rule](#minimal-taint-rule)
- [Sources](#sources)
- [Sinks](#sinks)
- [Sanitizers](#sanitizers)
- [Propagators](#propagators)
- [Exact Matching](#exact-matching)
- [Side-Effect Taint](#side-effect-taint)
- [Cross-Function Analysis](#cross-function-analysis)
- [Higher-Order Functions](#higher-order-functions)
- [Collection and Builder Methods](#collection-and-builder-methods)
- [Metavariables and Messages](#metavariables-and-messages)
- [Noise-Reduction Options](#noise-reduction-options)
- [Features to Verify Before Use](#features-to-verify-before-use)
- [SAST Rule Patterns](#sast-rule-patterns)
- [Troubleshooting](#troubleshooting)

## Minimal Taint Rule

Add `mode: taint` to enable taint operators. A practical taint rule should have
at least one source and one sink.

```yaml
rules:
  - id: python-flask-sql-injection
    mode: taint
    languages:
      - python
    severity: HIGH
    message: Request-controlled data reaches a SQL execution sink.
    pattern-sources:
      - pattern: request.args.get(...)
      - pattern: request.form.get(...)
      - pattern: request.values.get(...)
    pattern-sanitizers:
      - pattern: sqlparams.SQLParams(...).format(...)
        exact: true
    pattern-sinks:
      - pattern: $CURSOR.execute($QUERY, ...)
```

Each taint operator takes a list of formula entries. Each entry can use normal
rule formula syntax such as `pattern`, `patterns`, `pattern-either`, or
`pattern-regex`.

Common taint operators:

- `pattern-sources`: expressions or l-values where taint begins.
- `pattern-sinks`: expressions or arguments that become findings when tainted.
- `pattern-sanitizers`: expressions or l-values that clear taint.
- `pattern-propagators`: custom data movement not modeled by default.

## Sources

Sources mark data as tainted. Use sources for request parameters, headers,
cookies, environment variables, file contents, message queues, CLI arguments,
database values from untrusted tables, and framework-specific input helpers.

```yaml
pattern-sources:
  - pattern-either:
      - pattern: flask.request.args.get(...)
      - pattern: flask.request.form.get(...)
      - pattern: flask.request.headers.get(...)
```

Make sources as specific as possible. A broad source such as `$REQ` can make a
whole request object tainted and flood the rule with low-signal flows. Prefer
the field or accessor that returns attacker-controlled data.

Use `patterns` inside a source entry when a source needs context:

```yaml
pattern-sources:
  - patterns:
      - pattern-inside: |
          def $HANDLER(...):
              ...
      - pattern: |
          request.json[$KEY]
```

## Sinks

Sinks are dangerous operations whose selected argument or expression should not
receive tainted data.

```yaml
pattern-sinks:
  - pattern-either:
      - pattern: subprocess.$RUN($CMD, ..., shell=True, ...)
      - pattern: os.system($CMD)
```

For most SAST rules, match the sink call and let OpenGrep decide whether the
relevant argument is tainted. Add `focus-metavariable` in the sink formula when
only one argument is dangerous:

```yaml
pattern-sinks:
  - patterns:
      - pattern: |
          redirect($TARGET, ...)
      - focus-metavariable: $TARGET
```

This avoids findings where other arguments to the same call are tainted but not
security-relevant.

## Sanitizers

Sanitizers remove taint when data has been validated, encoded, escaped, or
converted into a safe representation for the specific sink.

```yaml
pattern-sanitizers:
  - pattern: html.escape(...)
    exact: true
  - pattern: markupsafe.escape(...)
    exact: true
```

Only model a sanitizer when it is safe for the sink in this rule. HTML escaping
does not sanitize SQL, path normalization does not sanitize shell commands, and
allow-list validation for one route may not be valid for another route.

Prefer `exact: true` for sanitizer calls so the sanitizer expression is clean
without treating every nested subexpression as clean.

Use side-effect sanitizers for validators that update or narrow an existing
variable in place:

```yaml
pattern-sanitizers:
  - patterns:
      - pattern: |
          ensure_safe_path($PATH)
      - focus-metavariable: $PATH
    by-side-effect: true
```

## Propagators

OpenGrep propagates taint through ordinary assignments, many expressions, and
function-call returns. Use custom propagators when a framework or library moves
data in a way the engine cannot infer from syntax alone.

```yaml
pattern-propagators:
  - pattern: |
      $BUILDER.append($VALUE)
    from: $VALUE
    to: $BUILDER
```

`from` is the tainted value. `to` is the destination that should become tainted.
By default, propagators are side-effecting: taint flows into the destination
l-value after the propagator call.

Set `by-side-effect: false` when the call returns a tainted value but should not
mark the receiver or destination as tainted:

```yaml
pattern-propagators:
  - pattern: |
      merge($BASE, $VALUE)
    from: $VALUE
    to: $BASE
    by-side-effect: false
```

Write propagators only for behavior that matters to the rule. Over-modeling
general framework APIs can create surprising flows.

## Exact Matching

`exact` controls whether subexpressions inside a matched formula also receive
the source, sink, or sanitizer meaning.

Sources and sanitizers are broad by default. If a source pattern matches
`source(sink(x))`, non-exact source matching can make nested pieces tainted too.
Prefer explicitness:

```yaml
pattern-sources:
  - pattern: read_user_input(...)
    exact: true
```

Sinks are exact by default. This is usually what you want because the sink call
is only a finding when the relevant argument or expression is tainted.

Use `exact: false` on sinks when a tainted subexpression inside the sink formula
should be enough to report:

```yaml
pattern-sinks:
  - pattern: |
      render(<... $EXPR ...>)
    exact: false
```

Make non-default exactness visible in the rule. It has a large effect on false
positives and false negatives.

## Side-Effect Taint

Use `by-side-effect` when a source or sanitizer mutates an existing l-value.
The formula must focus on the variable or field that should become tainted or
clean.

```yaml
pattern-sources:
  - patterns:
      - pattern: |
          decode_untrusted($BUF)
      - focus-metavariable: $BUF
    by-side-effect: true
```

This models:

```python
buf = {}
decode_untrusted(buf)
sink(buf)
```

Use `by-side-effect: only` when the later l-value should be tainted, but the
source occurrence itself should not be treated as tainted:

```yaml
pattern-sources:
  - patterns:
      - pattern: |
          fill_from_request($TARGET)
      - focus-metavariable: $TARGET
    by-side-effect: only
```

For side-effect sanitizers, focus the same l-value that is cleaned:

```yaml
pattern-sanitizers:
  - patterns:
      - pattern: |
          validate_redirect_target($URL)
      - focus-metavariable: $URL
    by-side-effect: true
```

## Cross-Function Analysis

By default, taint analysis is most reliable within a single function or method.
Run OpenGrep with `--taint-intrafile` when the flow crosses functions in the
same file.

```powershell
opengrep scan -c rules/taint.yaml src --taint-intrafile
```

`--taint-intrafile` enables cross-function analysis within one file. Confirmed
coverage includes:

- return values from helper functions;
- constructor arguments into fields;
- field assignment followed by later field reads;
- calls across methods on the same object;
- multi-hop flows through several functions;
- nested functions;
- functions defined after their callers;
- variadic and rest parameters;
- many higher-order function patterns.

It does not imply cross-file analysis. Keep rules useful without relying on
whole-program knowledge, and add local test cases for any cross-function flow a
rule is meant to catch.

Known limitation: inheritance-based flows are not confirmed by the OpenGrep
intrafile tutorial. If a finding depends on taint assigned in a base class and
read in a child class, expect possible false negatives until tested locally.

## Higher-Order Functions

With `--taint-intrafile`, OpenGrep models many higher-order flows where tainted
data enters a callback, lambda, closure, block, or named function reference.

Example JavaScript flow:

```javascript
const values = [req.query.name];
values.map((value) => {
  log.info(value);
});
```

Rule sketch:

```yaml
rules:
  - id: javascript-tainted-log-through-callback
    mode: taint
    languages:
      - javascript
      - typescript
    severity: MEDIUM
    message: Request data reaches a log sink through a callback.
    pattern-sources:
      - pattern: $REQ.query.$KEY
      - pattern: $REQ.body.$KEY
    pattern-sinks:
      - pattern: $LOG.$LEVEL($VALUE, ...)
```

Run with `--taint-intrafile` when expecting taint to enter callbacks through
`map`, `flatMap`, `filter`, `forEach`, `find`, `some`, `every`, `reduce`, named
callback references, or custom higher-order helpers.

Confirmed higher-order support covers common constructs across JavaScript,
TypeScript, Python, Ruby, PHP, Java streams, Kotlin, Swift, Scala, C#, Rust,
Julia, C++, and Elixir. Treat exact library coverage as version-dependent and
test the target language directly.

## Collection and Builder Methods

OpenGrep includes built-in taint models for common mutator and accessor methods
on collections and builder-like objects.

The two important model shapes are:

- Argument taints receiver: `list.add(item)`, `map.put(key, value)`,
  `builder.append(value)`.
- Receiver taints return: `list.pop()`, `map.get(key)`, `builder.toString()`.

This lets OpenGrep follow flows such as:

```python
items = []
items.append(request.args.get("name"))
send_to_sink(items)
```

and:

```javascript
const values = new Map();
values.set("name", req.query.name);
sink(values.get("name"));
```

Built-in collection modeling is confirmed for common methods in Java,
JavaScript and TypeScript, Python, Ruby, C#, Kotlin, Swift, Rust, Scala, and Go
sync maps. Add custom propagators only when a project-specific collection,
builder, or framework wrapper is not modeled by OpenGrep.

## Metavariables and Messages

Metavariables in sources, sinks, and sanitizers are independent by default. A
source metavariable and a sink metavariable with the same name do not
automatically mean the same code.

In messages, prefer metavariables bound by the sink:

```yaml
message: Request-controlled data reaches command execution in $CMD.
pattern-sinks:
  - patterns:
      - pattern: subprocess.run($CMD, ..., shell=True, ...)
      - focus-metavariable: $CMD
```

Use `taint_unify_mvars: true` only when source and sink metavariables must be
syntactically identical:

```yaml
options:
  taint_unify_mvars: true
```

This is uncommon in vulnerability rules. It can accidentally suppress real
flows where the value changes names along the path.

## Noise-Reduction Options

Use these `options:` keys when a taint rule is correct in spirit but too noisy.
Test each option against positive and negative cases because they can hide real
flows.

```yaml
options:
  taint_assume_safe_indexes: true
  taint_assume_safe_functions: true
```

Common options:

- `taint_assume_safe_indexes: true`: A tainted index does not make
  `collection[index]` tainted unless the collection itself is tainted.
- `taint_assume_safe_functions: true`: Unknown function calls do not propagate
  argument taint to their return value.
- `taint_only_propagate_through_assignments: true`: Disable implicit propagation
  except through direct assignments. Add explicit propagators for anything else.
- `taint_assume_safe_booleans: true`: Treat boolean expressions as clean when
  their type can be inferred.
- `taint_assume_safe_numbers: true`: Treat numeric expressions as clean when
  their type can be inferred.

Use explicit sanitizers when only one project helper is safe. Use options when
the same noisy propagation rule affects the whole rule.

## Features to Verify Before Use

The following keys or behaviors were not confirmed by the OpenGrep wiki pages
used for this reference. Do not add them to shared rules unless the installed
OpenGrep version accepts them and rule tests prove the expected behavior:

- `control: true` on taint sources;
- `at-exit: true` on taint sinks;
- taint `label` and `requires` formulas;
- interfile taint through `options: { interfile: true }`;
- inheritance-aware `--taint-intrafile` flows.

When a rule needs one of these capabilities, add a small local fixture and run
`opengrep scan -c rule.yaml fixture --taint-intrafile --json` to confirm the
actual engine behavior before relying on it.

## SAST Rule Patterns

### Command Injection

```yaml
rules:
  - id: python-request-to-shell
    mode: taint
    languages:
      - python
    severity: CRITICAL
    message: Request-controlled data reaches a shell command.
    pattern-sources:
      - pattern-either:
          - pattern: request.args.get(...)
          - pattern: request.form.get(...)
          - pattern: request.json[$KEY]
    pattern-sanitizers:
      - pattern: build_allowlisted_command(...)
        exact: true
    pattern-sinks:
      - patterns:
          - pattern: subprocess.$RUN($CMD, ..., shell=True, ...)
          - focus-metavariable: $CMD
      - pattern: os.system(...)
```

### Open Redirect

```yaml
rules:
  - id: javascript-express-open-redirect
    mode: taint
    languages:
      - javascript
      - typescript
    severity: HIGH
    message: Request-controlled data reaches a redirect target.
    pattern-sources:
      - pattern-either:
          - pattern: $REQ.query.$KEY
          - pattern: $REQ.body.$KEY
          - pattern: $REQ.params.$KEY
    pattern-sanitizers:
      - pattern: safeRedirectTarget(...)
        exact: true
    pattern-sinks:
      - patterns:
          - pattern: $RES.redirect($TARGET)
          - focus-metavariable: $TARGET
```

### Path Traversal Through a Builder

```yaml
rules:
  - id: java-path-traversal-builder
    mode: taint
    languages:
      - java
    severity: HIGH
    message: Request-controlled data is used to build a filesystem path.
    pattern-sources:
      - pattern: (HttpServletRequest $REQ).getParameter(...)
    pattern-sanitizers:
      - pattern: safePathFromBase($BASE, $NAME)
        exact: true
    pattern-propagators:
      - pattern: |
          $BUILDER.append($VALUE)
        from: $VALUE
        to: $BUILDER
    pattern-sinks:
      - pattern-either:
          - pattern: new FileInputStream($PATH)
          - pattern: Files.readString($PATH, ...)
```

### Side-Effect Validation

```yaml
rules:
  - id: python-validated-path-required
    mode: taint
    languages:
      - python
    severity: HIGH
    message: Unvalidated request path reaches file read.
    pattern-sources:
      - pattern: request.args.get(...)
        exact: true
    pattern-sanitizers:
      - patterns:
          - pattern: |
              assert_safe_path($PATH)
          - focus-metavariable: $PATH
        by-side-effect: true
    pattern-sinks:
      - pattern: open($PATH, ...)
```

## Troubleshooting

If a taint rule misses an expected finding:

- Confirm the source pattern matches the source expression by turning it into a
  temporary search rule.
- Confirm the sink pattern matches the sink call and focuses the dangerous
  argument when needed.
- Run with `--taint-intrafile` for cross-function, constructor, field,
  callback, collection, or variadic flows within one file.
- Add a custom propagator when a project-specific API stores tainted data into
  an object, builder, map, list, or context object.
- Check whether `exact: true` prevents taint from reaching a nested expression.
- Remove broad sanitizers and retest; an overbroad sanitizer can hide the flow.
- Disable noise-reduction options temporarily to see whether one is suppressing
  the match.
- Reduce the fixture to one source, one propagation step, and one sink, then add
  complexity back one step at a time.

If a taint rule reports too much:

- Make sources more specific.
- Add `focus-metavariable` to sinks so only the dangerous argument matters.
- Prefer `exact: true` on sources and sanitizers.
- Add precise sanitizers for project-approved validation helpers.
- Use `taint_assume_safe_indexes` or `taint_assume_safe_functions` only after
  checking that true positives remain.
- Scope the rule with `paths:` when only certain frameworks or entrypoints are
  relevant.
