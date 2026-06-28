# OpenGrep Constant Propagation

Constant propagation lets OpenGrep reason about values that are known constants
at a specific program point. This helps rules match code that uses a named
constant, a local assignment, or a folded expression instead of writing the
literal directly at the sink.

Use this reference when a rule depends on a literal value, a numeric threshold,
a boolean flag, or a string value that may be stored in a variable before use.

## Contents

- [What It Does](#what-it-does)
- [Literal Pattern Matching](#literal-pattern-matching)
- [`metavariable-comparison`](#metavariable-comparison)
- [Boolean, Numeric, and String Values](#boolean-numeric-and-string-values)
- [Mutable Values and Visibility](#mutable-values-and-visibility)
- [Disabling Constant Propagation](#disabling-constant-propagation)
- [SAST Rule Patterns](#sast-rule-patterns)
- [Troubleshooting](#troubleshooting)

## What It Does

OpenGrep can carry constant values through local assignments and simple
expressions when it can prove that a variable has one value at the match point.
For rule authors, this usually affects two things:

- A pattern containing a literal can match code that passes a constant variable
  with the same value.
- `metavariable-comparison` can evaluate a metavariable bound to a constant
  variable, not only a literal written inline.

Constant propagation commonly applies to booleans, numbers, and strings. Treat
the exact scope as language- and version-dependent; prefer rules that still
make sense when only same-file, local constants are available.

## Literal Pattern Matching

A literal pattern can match a variable when OpenGrep can prove the variable's
constant value.

```yaml
rules:
  - id: python-flask-debug-constant
    languages:
      - python
    severity: HIGH
    message: Flask debug mode is enabled through a constant value.
    pattern: |
      $APP.run(..., debug=True, ...)
```

This should match both direct and propagated values:

```python
app.run(debug=True)

DEBUG_MODE = True
app.run(debug=DEBUG_MODE)
```

Constant folding can also help when the literal is produced by a simple
constant expression:

```yaml
rules:
  - id: javascript-long-session-cookie
    languages:
      - javascript
    severity: MEDIUM
    message: Session cookie lifetime is set to one year.
    pattern: |
      maxAge: 31536000000
```

This can match:

```javascript
const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;
cookieOptions = { maxAge: ONE_YEAR_MS };
```

Keep literal patterns narrow. A literal such as `true` or `0` by itself is too
broad; anchor it to the security-relevant API, option name, or object field.

## `metavariable-comparison`

Use `metavariable-comparison` when the value must satisfy a condition rather
than equal one exact literal.

```yaml
rules:
  - id: python-privileged-port
    languages:
      - python
    severity: MEDIUM
    message: Application binds to a privileged port.
    patterns:
      - pattern: |
          $APP.run(..., port=$PORT, ...)
      - metavariable-comparison:
          metavariable: $PORT
          comparison: $PORT < 1024
```

This can match either form:

```python
app.run(port=80)

ADMIN_PORT = 443
app.run(port=ADMIN_PORT)
```

Use `int()` or `str()` inside the comparison when the capture is source text
that needs conversion:

```yaml
patterns:
  - pattern: |
      os.chmod($PATH, $MODE)
  - metavariable-comparison:
      metavariable: $MODE
      comparison: int($MODE) > 0o600
```

When comparing strings, remember that the metavariable may bind to a literal
value or to source text depending on what OpenGrep can prove. Test both cases.

```yaml
rules:
  - id: python-hardcoded-admin-role
    languages:
      - python
    severity: MEDIUM
    message: Hardcoded administrative role is passed to access-checking code.
    patterns:
      - pattern: |
          require_role($ROLE)
      - metavariable-comparison:
          metavariable: $ROLE
          comparison: $ROLE == "admin"
```

## Boolean, Numeric, and String Values

### Boolean Flags

Boolean constants are useful for finding insecure feature flags:

```yaml
rules:
  - id: python-requests-verify-disabled-constant
    languages:
      - python
    severity: HIGH
    message: TLS certificate verification is disabled.
    pattern: |
      requests.$METHOD(..., verify=False, ...)
```

This can match:

```python
VERIFY_CERTS = False
requests.get(url, verify=VERIFY_CERTS)
```

### Numeric Thresholds

Numeric constants are useful for permissions, ports, cryptographic sizes, retry
limits, and timeout thresholds:

```yaml
rules:
  - id: python-small-rsa-key
    languages:
      - python
    severity: HIGH
    message: RSA key size is below 2048 bits.
    patterns:
      - pattern: |
          rsa.generate_private_key(..., key_size=$SIZE, ...)
      - metavariable-comparison:
          metavariable: $SIZE
          comparison: $SIZE < 2048
```

### String Values

String constants are useful for algorithms, modes, domains, roles, and feature
names:

```yaml
rules:
  - id: java-weak-cipher-transformation
    languages:
      - java
    severity: HIGH
    message: ECB mode is selected through a constant string.
    pattern: |
      Cipher.getInstance("AES/ECB/PKCS5Padding")
```

This can match a local string constant when the value is provable:

```java
String transformation = "AES/ECB/PKCS5Padding";
Cipher.getInstance(transformation);
```

## Mutable Values and Visibility

Constant propagation is conservative when a value could be changed elsewhere.
This is most visible with mutable objects, public fields, globals, and values
passed to code that may mutate them.

If a value is publicly writable, OpenGrep may avoid treating it as constant:

```java
import java.util.regex.Pattern;

public String REDOS_PATTERN = "(a+)+$";

class Handler {
  void compile() {
    Pattern.compile(REDOS_PATTERN);
  }
}
```

A private or final value gives the analyzer stronger evidence:

```java
import java.util.regex.Pattern;

private final String REDOS_PATTERN = "(a+)+$";

class Handler {
  void compile() {
    Pattern.compile(REDOS_PATTERN);
  }
}
```

Be extra careful in languages where strings or collection-like values can be
mutated. If a function or method call may change a value, propagation can stop
or produce surprising results. Method calls whose return value is ignored are
especially likely to be treated as possible mutation points.

## Disabling Constant Propagation

Constant propagation is useful by default for most SAST rules, but disable it
when exact source spelling matters or when propagation creates too much noise.

```yaml
rules:
  - id: python-direct-debug-literal-only
    languages:
      - python
    severity: MEDIUM
    message: Debug mode is written directly as a literal.
    options:
      constant_propagation: false
    pattern: |
      $APP.run(..., debug=True, ...)
```

Reasons to disable it:

- The rule is meant to find only direct literal usage.
- Constants from generated code or framework defaults create low-signal matches.
- A migration rule needs to rewrite the exact matched text and propagated values
  would make the fix unsafe.
- You are debugging whether a result comes from structural matching or from
  propagated values.

## SAST Rule Patterns

### Insecure Options Hidden Behind Constants

```yaml
rules:
  - id: javascript-jwt-none-algorithm
    languages:
      - javascript
      - typescript
    severity: HIGH
    message: JWT verification allows the none algorithm through a constant.
    pattern: |
      jwt.verify(..., { ..., algorithms: [..., "none", ...], ... })
```

This can catch:

```javascript
const ALGORITHM = "none";
jwt.verify(token, key, { algorithms: [ALGORITHM] });
```

### Numeric Policy Values

```yaml
rules:
  - id: go-low-bcrypt-cost
    languages:
      - go
    severity: MEDIUM
    message: bcrypt cost is below the recommended minimum.
    patterns:
      - pattern: |
          bcrypt.GenerateFromPassword($PASSWORD, $COST)
      - metavariable-comparison:
          metavariable: $COST
          comparison: $COST < 10
```

This can catch:

```go
const weakCost = 8
bcrypt.GenerateFromPassword(password, weakCost)
```

### Constant Through a Local Alias

```yaml
rules:
  - id: python-django-debug-enabled
    languages:
      - python
    severity: HIGH
    message: Django DEBUG is enabled.
    pattern: |
      DEBUG = True
```

For settings built from aliases, match the sink and let propagation resolve the
value:

```yaml
rules:
  - id: python-django-debug-config-object
    languages:
      - python
    severity: HIGH
    message: Django debug setting resolves to true.
    pattern: |
      config.DEBUG = True
```

This can match:

```python
ENABLE_DEBUG = True
config.DEBUG = ENABLE_DEBUG
```

## Troubleshooting

If a constant-dependent rule does not match:

- Confirm the value is one of the supported constant kinds: boolean, number, or
  string-like value.
- Check whether the value can be reassigned, mutated, exported, or modified by a
  method call.
- Reduce the example to a single file and a direct assignment before testing
  longer flows.
- Verify the language parser supports the syntax in the target file.
- Add an explicit literal test case and a propagated-constant test case.
- Use `options: { constant_propagation: false }` temporarily to see whether a
  surprising match depends on propagation.
- Avoid relying on cross-file constants unless the installed OpenGrep version
  and scan configuration are known to support that analysis.

When in doubt, write the rule so the positive pattern identifies the risky sink,
then use `metavariable-comparison` or a literal option pattern to refine the
specific constant value.
