# OpenGrep Symbolic Propagation

Symbolic propagation lets a rule match through intermediate variable
assignments. Instead of writing every aliasing variant by hand, enable
`options: { symbolic_propagation: true }` and write the direct expression shape
you care about.

Use it when the same expression is often split across temporary variables, such
as method chains, object fields, request accessors, builder expressions, or size
calculations. Treat it as an experimental rule option: useful, but worth testing
with small fixtures before relying on it in shared SAST rule packs.

## Contents

- [What It Does](#what-it-does)
- [Enable It Per Rule](#enable-it-per-rule)
- [How It Differs From Other Data Flow](#how-it-differs-from-other-data-flow)
- [Common Matching Shapes](#common-matching-shapes)
- [Limitations](#limitations)
- [SAST Rule Patterns](#sast-rule-patterns)
- [Troubleshooting](#troubleshooting)

## What It Does

Symbolic propagation matches code modulo simple variable assignments. A pattern
for a direct expression can also match code where that expression is first saved
to a local variable and used later.

Rule:

```yaml
rules:
  - id: python-request-template-render
    languages:
      - python
    severity: HIGH
    message: Request data is rendered as a template string.
    options:
      symbolic_propagation: true
    pattern: |
      render_template_string(request.args.get(...))
```

Direct form:

```python
return render_template_string(request.args.get("template"))
```

Aliased form:

```python
template = request.args.get("template")
return render_template_string(template)
```

Without symbolic propagation, the aliased form usually needs an explicit
multi-statement pattern. With symbolic propagation, the direct expression
pattern can cover both.

## Enable It Per Rule

Enable symbolic propagation in `options`:

```yaml
options:
  symbolic_propagation: true
```

Keep it per rule rather than assuming it globally. It can broaden matches and
can make a rule slower or harder to reason about when the rule already uses wide
patterns.

Use it with normal structural operators:

```yaml
rules:
  - id: javascript-request-body-to-innerhtml
    languages:
      - javascript
      - typescript
    severity: HIGH
    message: Request body data is assigned to innerHTML.
    options:
      symbolic_propagation: true
    patterns:
      - pattern: |
          $EL.innerHTML = $REQ.body.$FIELD
      - pattern-not-inside: |
          sanitizeHtml(...)
```

This can match:

```javascript
const value = req.body.comment;
element.innerHTML = value;
```

## How It Differs From Other Data Flow

Symbolic propagation is expression substitution, not vulnerability tainting.

- Constant propagation tracks known literal values such as `True`, `443`, or
  `"AES/ECB/PKCS5Padding"`.
- Symbolic propagation tracks expression aliases such as `tmp = req.body.name`
  or `idx = user.profile.id`.
- Taint analysis tracks untrusted data through assignments, calls,
  propagators, sanitizers, and sinks.

Use symbolic propagation for concise structural rules. Use taint mode when the
bug depends on a source-to-sink flow with sanitizers or several propagation
steps.

Example where symbolic propagation is enough:

```yaml
pattern: |
  redirect(request.args.get(...))
options:
  symbolic_propagation: true
```

Example where taint mode is usually better:

```python
target = request.args.get("next")
target = normalize(target)
if is_allowed_redirect(target):
    redirect(target)
```

The second case needs sanitizer modeling and path reasoning; do not try to force
symbolic propagation to behave like taint analysis.

## Common Matching Shapes

### Method Chains Split Across Temporaries

```yaml
rules:
  - id: java-disable-hostname-verification
    languages:
      - java
    severity: HIGH
    message: Hostname verification is disabled.
    options:
      symbolic_propagation: true
    pattern: |
      $CLIENT.hostnameVerifier(NoopHostnameVerifier.INSTANCE)
```

Can match:

```java
var verifier = NoopHostnameVerifier.INSTANCE;
client.hostnameVerifier(verifier);
```

### Field or Property Access Aliases

```yaml
rules:
  - id: javascript-cookie-without-secure
    languages:
      - javascript
      - typescript
    severity: MEDIUM
    message: Cookie options explicitly disable the secure flag.
    options:
      symbolic_propagation: true
    pattern: |
      $RES.cookie($NAME, $VALUE, { ..., secure: false, ... })
```

Can match:

```javascript
const options = { secure: false, httpOnly: true };
res.cookie("sid", sid, options);
```

### Expression Aliases in Arguments

```yaml
rules:
  - id: go-request-path-file-read
    languages:
      - go
    severity: HIGH
    message: Request path is passed to a file read.
    options:
      symbolic_propagation: true
    pattern: |
      os.ReadFile($REQ.URL.Query().Get("path"))
```

Can match:

```go
path := r.URL.Query().Get("path")
data, err := os.ReadFile(path)
```

### Size or Offset Calculations

```yaml
rules:
  - id: c-size-multiplied-before-allocation
    languages:
      - c
      - cpp
    severity: MEDIUM
    message: Allocation size is derived from multiplication; review for overflow.
    options:
      symbolic_propagation: true
    pattern-either:
      - pattern: malloc($N * $SIZE)
      - pattern: calloc($N, $SIZE)
```

Can match:

```c
size_t bytes = count * sizeof(struct item);
void *p = malloc(bytes);
```

## Limitations

Symbolic propagation is intentionally limited.

- It must be enabled explicitly with `options: symbolic_propagation: true`.
- It does not reliably cross branch boundaries such as `if`, `switch`, loops,
  or exception paths.
- It is not a substitute for taint mode, sanitizers, or custom propagators.
- It is most useful inside a local function or method body. Verify behavior
  before assuming cross-function matching.
- Reassignment, mutation, aliasing through references, and side-effecting calls
  can stop or confuse propagation.
- It can create surprising matches when a broad pattern is enabled on a large
  codebase.
- It may affect runtime on complex rules; scope with `paths` and precise
  patterns.

Example branch limitation:

```python
if cond:
    template = request.args.get("template")
else:
    template = "safe.html"

render_template_string(template)
```

Do not assume symbolic propagation will prove which branch reaches the sink. Use
taint analysis or a more explicit pattern when branch-sensitive behavior matters.

## SAST Rule Patterns

### Open Redirect Alias

```yaml
rules:
  - id: python-flask-open-redirect-symbolic
    languages:
      - python
    severity: HIGH
    message: Request parameter is used as a redirect target.
    options:
      symbolic_propagation: true
    pattern: |
      redirect(request.args.get(...))
```

Matches:

```python
target = request.args.get("next")
return redirect(target)
```

Use taint mode instead when the application has allow-list helpers or redirect
sanitizers that must be modeled.

### Insecure Deserialization Alias

```yaml
rules:
  - id: python-pickle-request-data-symbolic
    languages:
      - python
    severity: CRITICAL
    message: Request body data is deserialized with pickle.
    options:
      symbolic_propagation: true
    pattern: |
      pickle.loads(request.get_data(...))
```

Matches:

```python
body = request.get_data()
return pickle.loads(body)
```

### Unsafe HTML Assignment Alias

```yaml
rules:
  - id: typescript-location-hash-innerhtml
    languages:
      - typescript
      - javascript
    severity: HIGH
    message: Location hash is assigned to innerHTML.
    options:
      symbolic_propagation: true
    pattern: |
      $EL.innerHTML = window.location.hash
```

Matches:

```typescript
const fragment = window.location.hash;
preview.innerHTML = fragment;
```

### Insecure TLS Option Alias

```yaml
rules:
  - id: javascript-https-reject-unauthorized-disabled
    languages:
      - javascript
      - typescript
    severity: HIGH
    message: TLS certificate verification is disabled.
    options:
      symbolic_propagation: true
    pattern: |
      https.request({ ..., rejectUnauthorized: false, ... })
```

Matches:

```javascript
const tlsOptions = { rejectUnauthorized: false };
https.request(tlsOptions);
```

## Troubleshooting

If a symbolic-propagation rule misses a case:

- Confirm the direct pattern matches the fully inlined expression first.
- Add `options: { symbolic_propagation: true }` to the same rule that contains
  the direct pattern.
- Reduce the fixture to one assignment and one use in the same block.
- Check for branches, loops, reassignments, or method calls between assignment
  and use.
- Use taint mode when the flow spans sanitizers, helper functions, callbacks,
  or project-specific containers.
- Add explicit multi-statement patterns for important cases that symbolic
  propagation does not cover.

If a rule reports too much:

- Narrow the direct expression pattern.
- Add `pattern-not` or `pattern-not-inside` for common safe wrappers.
- Scope the rule with `paths`.
- Disable symbolic propagation and compare results to see which matches depend
  on assignment expansion.
- Prefer taint mode when the real vulnerability requires source and sanitizer
  reasoning rather than expression-shape matching.
