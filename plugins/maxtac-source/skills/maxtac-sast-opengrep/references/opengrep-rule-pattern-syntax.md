# OpenGrep Pattern Syntax

Use OpenGrep patterns to describe source code shapes directly. Patterns can be
small expressions, full statements, class or function fragments, or coordinated
sets of patterns in YAML rules.

## Contents

- [Pattern Basics](#pattern-basics)
- [Ellipsis](#ellipsis)
- [Metavariables](#metavariables)
- [Typed Metavariables](#typed-metavariables)
- [Equivalences](#equivalences)
- [Deep Expression Operator](#deep-expression-operator)
- [Partial Constructs and Limits](#partial-constructs-and-limits)
- [Deprecated String Matching](#deprecated-string-matching)
- [SAST Pattern Tips](#sast-pattern-tips)

## Pattern Basics

OpenGrep matches code by structure, not just raw text. An expression pattern can
match a standalone expression or the same expression nested inside a larger one:

```yaml
pattern: |
  decrypt($DATA, "ECB")
```

This can match code such as:

```python
result = decrypt(payload, "ECB")
log(decrypt(secret, "ECB"))
```

A statement pattern can match at the top level of a block or inside nested
control flow:

```yaml
pattern: |
  return render_template_string($TEMPLATE)
```

## Ellipsis

Use `...` to match zero or more items in the current syntactic context:
arguments, statements, parameters, fields, list elements, object entries, string
characters, or similar sequences.

### Calls and Arguments

Match a call regardless of its arguments:

```yaml
pattern: |
  eval(...)
```

Match a specific argument wherever it appears:

```yaml
pattern: |
  requests.get(..., verify=False, ...)
```

Match arguments before or after an anchor:

```yaml
pattern: |
  spawn_process(..., shell=True)
```

An ellipsis in a call matches zero or more arguments, so `danger(...)` matches
`danger()`, `danger(input)`, and `danger(input, options)`. Use a metavariable
such as `danger($ARG)` when exactly one argument is required.

### Method Calls and Chains

Use metavariables for receivers:

```yaml
pattern: |
  $ARCHIVE.extractall(...)
```

Use `...` inside a chain to skip intermediate calls:

```yaml
pattern: |
  $REQ.getUser(). ... .isAdmin()
```

### Definitions and Blocks

Match function definitions by parameter list and body shape:

```yaml
pattern: |
  def $FUNC(..., $ARG=[], ...):
      ...
```

Match any JavaScript function with one parameter:

```yaml
pattern: |
  function ...($INPUT) { ... }
```

Match classes with a specific base class:

```yaml
pattern: |
  class $HANDLER(UnsafeBaseHandler):
      ...
```

The ellipsis stays in its syntactic scope. In a multi-statement pattern, it can
move forward through the current block and nested child blocks, but it does not
jump from an inner block back out to a sibling outer block.

### Strings, Regex Literals, and Containers

Use `"..."` to match any string literal content:

```yaml
pattern: |
  set_secret_key("...")
```

Use `/.../` for any regular-expression literal in languages that have regex
literal syntax:

```yaml
pattern: |
  denylist = /.../
```

Use ellipses inside arrays, maps, objects, and dictionaries:

```yaml
pattern: |
  permissions = [..., "admin", ...]
```

```yaml
pattern: |
  config = {..., "debug": True, ...}
```

You can also match only a key-value pair in structured data:

```yaml
pattern: |
  "allowInsecure": true
```

### Binary Operations and Single Items

Ellipses can stand for repeated operands in a binary expression:

```yaml
pattern: |
  $MASK = READ | WRITE | ...
```

In some contexts, `...` can also match one item rather than a sequence:

```yaml
pattern: |
  if (...) {
    audit();
  }
```

## Metavariables

Metavariables bind part of the matched code for later constraints, messages, or
fixes. They start with `$` and use uppercase letters, digits, and underscores:
`$X`, `$REQUEST`, `$ARG_1`.

```yaml
pattern: |
  $LEFT + $RIGHT
```

Metavariables can match many syntactic categories, including expressions,
identifiers, imports, exceptions, receivers, arguments, and class names:

```yaml
pattern: |
  import $MODULE
```

Reusing the same metavariable name requires the same code to appear in each
position:

```yaml
pattern: |
  $USER = get_user(...)
  ...
  delete_user($USER)
```

Use literal metavariables to capture the contents of literals:

```yaml
pattern: |
  connect("$URL")
```

The message can display captured metavariables:

```yaml
message: Connection target is $URL
```

Use an ellipsis metavariable to capture a sequence:

```yaml
pattern: |
  log($...ARGS)
message: Logging arguments: $...ARGS
```

Use `$_` when the value must exist but does not matter:

```yaml
pattern: |
  set_cookie($_, $_, secure=False)
```

Metavariables with the same name unify within a `patterns` block. In taint-mode
rules, metavariables unify within sources and within sinks; to require a source
and sink metavariable with the same name to refer to the same code, set the rule
option `taint_unify_mvars: true`.

## Typed Metavariables

Typed metavariables constrain a capture to a declared or inferred type. Type
support is language dependent and usually most reliable for local variables and
parameters within a single file.

Java-style syntax places the type before the metavariable:

```yaml
pattern: |
  (java.sql.Statement $STMT).executeQuery($QUERY)
```

C-style syntax can constrain either side of an expression:

```yaml
pattern: |
  strcmp((char *$A), (char *$B))
```

Go uses a colon form:

```yaml
pattern: |
  ($FS : http.FileSystem).Open($NAME)
```

TypeScript uses a similar annotation form:

```yaml
pattern: |
  ($SANITIZER: DomSanitizer).bypassSecurityTrustHtml(...)
```

Typed matching is shallow. Avoid relying on it for deep field accesses,
container element types, or values whose type can only be proven across files.

## Equivalences

OpenGrep can match some code forms that are semantically equivalent to the
pattern.

Fully qualified names can match aliased or imported names:

```yaml
pattern: |
  subprocess.Popen(...)
```

This can match calls through imported aliases when the language parser can
resolve them.

Constant propagation can match calls where the literal appears through a local
constant:

```yaml
pattern: |
  set_password("password")
```

This can match:

```python
DEFAULT_PASSWORD = "password"
set_password(DEFAULT_PASSWORD)
```

Associative and commutative matching can account for reordered operands in
operators such as bitwise OR. Be careful with metavariables in these patterns:
they may bind to one operand or a grouped expression depending on the operator
and the number of possible matches.

## Deep Expression Operator

Use `<... PATTERN ...>` to find a pattern anywhere inside the current expression
tree.

```yaml
pattern: |
  if <... $USER.is_admin() ...>:
      ...
```

This matches conditions where the admin check is nested inside larger boolean
logic:

```python
if user.is_active() and user.is_admin() and tenant.enabled:
    allow()
```

Useful locations include:

- Conditions: `if <... $CHECK ...>:`
- Nested call arguments: `query(<... $SQL ...>)`
- Binary operands: `<... $A ...> + "suffix"`
- Other expression contexts where the risky subexpression may be buried.

## Partial Constructs and Limits

Patterns must be syntactically meaningful enough for the selected parser.

- A fragment such as `1 +` is invalid; write a complete expression like
  `1 + $X`.
- Statement-like patterns may also match expression contexts. For example,
  `foo()` can match a direct statement, an assignment RHS, or a call argument.
- Import statements are their own syntax. A bare `foo` expression pattern should
  not be expected to match `import foo`; use an import pattern.
- Partial statements have limited support. Headers such as `if ($COND)` or
  `try { ... }` can be useful with `pattern-inside`.
- Function and class headers can often be matched without writing the full body,
  such as `public void $METHOD(...)` or `class $NAME`.
- Half-written control-flow blocks are invalid. Include a body placeholder such
  as `...` or `$BODY`.
- An ellipsis in a statement sequence cannot cross from an inner block back out
  to an unrelated outer block.

## Deprecated String Matching

Avoid legacy string-regex syntax inside string literals, such as
`"=~/pattern/"`. Prefer `metavariable-regex`, `pattern-regex`, or a
`metavariable-pattern` with `language: generic` when inspecting literal content.

Example:

```yaml
patterns:
  - pattern: |
      redirect("$TARGET")
  - metavariable-regex:
      metavariable: $TARGET
      regex: '^https?://'
```

## SAST Pattern Tips

- Start with a narrow positive pattern around the vulnerable operation.
- Use `...` to tolerate irrelevant arguments or statements, but keep it inside
  the smallest useful syntactic scope.
- Use repeated metavariables for relationships, such as opening and later using
  the same file handle.
- Prefer typed metavariables when a common method name has safe and unsafe
  receivers.
- Add `pattern-not` or `pattern-not-inside` for common safe wrappers and test
  helpers.
- Put captured metavariables in messages only when they help triage the finding.
- Test every rule against positive and negative snippets for spacing, nesting,
  aliases, constants, comments, and framework-specific wrappers.
