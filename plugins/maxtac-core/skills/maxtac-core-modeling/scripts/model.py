#!/usr/bin/env python3
"""Create, validate, project, and search MaxTAC security models."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LEDGER_SCRIPTS_DIR = SCRIPT_DIR.parent.parent / "maxtac-core-ledger" / "scripts"
sys.path.insert(0, str(LEDGER_SCRIPTS_DIR))

try:
    import workspace_db  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover - local fallback for schema-only usage
    workspace_db = None  # type: ignore


DOCUMENT_TYPE = "maxtac.security_model"
SCHEMA_VERSION = "1.0"
STATUSES = ("candidate", "observed", "confirmed", "refuted", "stale")
CONFIDENCES = ("high", "medium", "low", "unknown")
EVIDENCE_REQUIRED_STATUSES = {"observed", "confirmed", "refuted", "stale"}
ENTITY_KINDS = (
    "actor",
    "principal",
    "component",
    "service",
    "resource",
    "asset",
    "entrypoint",
    "guard",
    "sink",
    "state",
    "boundary",
    "policy",
    "data-store",
    "message",
    "protocol",
    "role",
    "tenant",
    "build-artifact",
    "unknown",
)
COLLECTIONS = (
    "entities",
    "relations",
    "invariants",
    "formulas",
    "assumptions",
    "unknowns",
    "contradictions",
)
PREFIXES = {
    "entities": "ENT",
    "relations": "REL",
    "invariants": "INV",
    "formulas": "FOL",
    "assumptions": "ASM",
    "unknowns": "UNK",
    "contradictions": "CON",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slug(value: str, default: str = "model") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return cleaned or default


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{path}: expected a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_repeated(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for item in str(value).split(","):
            stripped = item.strip()
            if stripped and stripped not in result:
                result.append(stripped)
    return result


def parse_key_values(values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise SystemExit(f"expected KEY=VALUE: {value}")
        key, raw = value.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"empty property key: {value}")
        result[key] = raw.strip()
    return result


def model_path(root: Path, model_id: str) -> Path:
    return root / "models" / slug(model_id) / "model.json"


def root_for_model_path(path: Path) -> Path | None:
    resolved = path.resolve()
    if resolved.name == "model.json" and resolved.parent.parent.name == "models":
        return resolved.parent.parent.parent
    return None


def base_model(args: argparse.Namespace) -> dict[str, Any]:
    model_id = slug(args.model_id)
    timestamp = now()
    return {
        "document_type": DOCUMENT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "model_id": model_id,
        "created_at": timestamp,
        "updated_at": timestamp,
        "target": {
            "name": args.target,
            "kind": args.kind,
            "revision": args.revision or "",
            "source": args.source or "",
        },
        "scope": {
            "summary": args.summary or "",
            "include_paths": parse_repeated(args.include) or ["."],
            "exclude_paths": parse_repeated(args.exclude),
            "limitations": parse_repeated(args.limitation),
        },
        "entities": [],
        "relations": [],
        "invariants": [],
        "formulas": [],
        "assumptions": [],
        "unknowns": [],
        "contradictions": [],
    }


def collection(payload: dict[str, Any], name: str) -> list[dict[str, Any]]:
    value = payload.setdefault(name, [])
    if not isinstance(value, list):
        raise SystemExit(f"{name} must be an array")
    return value


def next_id(items: list[dict[str, Any]], collection_name: str) -> str:
    prefix = PREFIXES[collection_name]
    highest = 0
    pattern = re.compile(rf"{re.escape(prefix)}-(\d{{4}})$")
    for item in items:
        match = pattern.fullmatch(str(item.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:04d}"


def common_assertion(args: argparse.Namespace, item_id: str) -> dict[str, Any]:
    return {
        "id": item_id,
        "status": args.status,
        "confidence": getattr(args, "confidence", "unknown"),
        "evidence": parse_repeated(getattr(args, "evidence", None)),
        "tags": parse_repeated(getattr(args, "tag", None)),
        "properties": parse_key_values(getattr(args, "property", None)),
    }


def replace_or_append(items: list[dict[str, Any]], item: dict[str, Any], *, replace: bool) -> str:
    for index, existing in enumerate(items):
        if existing.get("id") == item["id"]:
            if not replace:
                raise SystemExit(f"item already exists: {item['id']}. Use --replace to update it.")
            items[index] = item
            return "replaced"
    items.append(item)
    return "added"


def balanced_parentheses(value: str) -> bool:
    count = 0
    for char in value:
        if char == "(":
            count += 1
        elif char == ")":
            count -= 1
        if count < 0:
            return False
    return count == 0


def id_index(payload: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in COLLECTIONS:
        for item in payload.get(name) or []:
            if isinstance(item, dict) and str(item.get("id", "")).strip():
                result[str(item["id"])] = name
    return result


def validate_item_common(
    item: dict[str, Any],
    where: str,
    errors: list[str],
    warnings: list[str],
    *,
    require_confidence: bool = True,
) -> None:
    item_id = str(item.get("id", "")).strip()
    if not item_id:
        errors.append(f"{where}.id is required")
    status = str(item.get("status", "")).strip()
    if status not in STATUSES:
        errors.append(f"{where}.status must be one of {', '.join(STATUSES)}")
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        errors.append(f"{where}.evidence must be an array")
        evidence_count = 0
    else:
        evidence_count = len([value for value in evidence if str(value).strip()])
    if status in EVIDENCE_REQUIRED_STATUSES and evidence_count == 0:
        errors.append(f"{where}.evidence is required when status is {status}")
    if require_confidence:
        confidence = str(item.get("confidence", "")).strip()
        if confidence not in CONFIDENCES:
            errors.append(f"{where}.confidence must be one of {', '.join(CONFIDENCES)}")
        if status == "confirmed" and confidence in {"low", "unknown"}:
            warnings.append(f"{where} is confirmed with {confidence} confidence")
    tags = item.get("tags", [])
    if tags is not None and not isinstance(tags, list):
        errors.append(f"{where}.tags must be an array")
    properties = item.get("properties", {})
    if properties is not None and not isinstance(properties, dict):
        errors.append(f"{where}.properties must be an object")


def require_text(item: dict[str, Any], where: str, key: str, errors: list[str]) -> None:
    if not str(item.get(key, "")).strip():
        errors.append(f"{where}.{key} is required")


def validate_model(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if payload.get("document_type") != DOCUMENT_TYPE:
        errors.append(f"document_type must be {DOCUMENT_TYPE}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not str(payload.get("model_id", "")).strip():
        errors.append("model_id is required")

    target = payload.get("target")
    if not isinstance(target, dict):
        errors.append("target must be an object")
    else:
        for key in ("name", "kind"):
            if not str(target.get(key, "")).strip():
                errors.append(f"target.{key} is required")

    scope = payload.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        for key in ("include_paths", "exclude_paths", "limitations"):
            if not isinstance(scope.get(key), list):
                errors.append(f"scope.{key} must be an array")

    ids = id_index(payload)
    seen_by_collection: dict[str, set[str]] = {name: set() for name in COLLECTIONS}
    for name in COLLECTIONS:
        items = payload.get(name)
        if not isinstance(items, list):
            errors.append(f"{name} must be an array")
            continue
        for index, item in enumerate(items):
            where = f"{name}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{where} must be an object")
                continue
            item_id = str(item.get("id", "")).strip()
            if item_id:
                if item_id in seen_by_collection[name]:
                    errors.append(f"{where}.id duplicates {item_id}")
                seen_by_collection[name].add(item_id)

            if name == "unknowns":
                validate_item_common(item, where, errors, warnings, require_confidence=False)
            elif name == "contradictions":
                validate_item_common(item, where, errors, warnings, require_confidence=False)
            else:
                validate_item_common(item, where, errors, warnings)

            if name == "entities":
                require_text(item, where, "kind", errors)
                require_text(item, where, "name", errors)
                require_text(item, where, "description", errors)
                kind = str(item.get("kind", "")).strip()
                if kind and kind not in ENTITY_KINDS:
                    warnings.append(f"{where}.kind is not a standard kind: {kind}")
            elif name == "relations":
                for key in ("subject", "predicate", "object", "statement", "description"):
                    require_text(item, where, key, errors)
                for key in ("subject", "object"):
                    ref = str(item.get(key, "")).strip()
                    if ref and ids.get(ref) != "entities":
                        errors.append(f"{where}.{key} must reference an entity id, got {ref}")
            elif name == "invariants":
                require_text(item, where, "statement", errors)
                require_text(item, where, "scope", errors)
                formula = str(item.get("formula", "")).strip()
                if formula and not balanced_parentheses(formula):
                    errors.append(f"{where}.formula has unbalanced parentheses")
                for ref in item.get("violated_by") or []:
                    if str(ref).strip() and str(ref).strip() not in ids:
                        warnings.append(f"{where}.violated_by references unknown assertion id: {ref}")
            elif name == "formulas":
                require_text(item, where, "formula", errors)
                require_text(item, where, "description", errors)
                formula = str(item.get("formula", "")).strip()
                if formula and not balanced_parentheses(formula):
                    errors.append(f"{where}.formula has unbalanced parentheses")
                for ref in item.get("derived_from") or []:
                    if str(ref).strip() and str(ref).strip() not in ids:
                        warnings.append(f"{where}.derived_from references unknown assertion id: {ref}")
            elif name == "assumptions":
                require_text(item, where, "statement", errors)
                require_text(item, where, "scope", errors)
            elif name == "unknowns":
                require_text(item, where, "question", errors)
                require_text(item, where, "scope", errors)
                for ref in item.get("blocked_by") or []:
                    if str(ref).strip() and str(ref).strip() not in ids:
                        warnings.append(f"{where}.blocked_by references unknown assertion id: {ref}")
            elif name == "contradictions":
                require_text(item, where, "statement", errors)
                refs = item.get("assertion_refs")
                if not isinstance(refs, list):
                    errors.append(f"{where}.assertion_refs must be an array")
                elif len(refs) < 2:
                    warnings.append(f"{where}.assertion_refs should name at least two conflicting assertions")
                else:
                    for ref in refs:
                        if str(ref).strip() and str(ref).strip() not in ids:
                            warnings.append(f"{where}.assertion_refs references unknown assertion id: {ref}")
    return errors, warnings


def index_model(path: Path, payload: dict[str, Any]) -> None:
    if workspace_db is None or not hasattr(workspace_db, "upsert_model"):
        return
    root = root_for_model_path(path)
    if root is None:
        return
    workspace_db.upsert_model(root, payload, path)


def save_model(path: Path, payload: dict[str, Any], *, validate_first: bool = True) -> None:
    payload["updated_at"] = now()
    if validate_first:
        errors, warnings = validate_model(payload)
        if errors:
            raise SystemExit("\n".join(errors))
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
    write_json(path, payload)
    index_model(path, payload)


def load_model_for_write(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    errors, warnings = validate_model(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return payload


def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = model_path(root, args.model_id)
    if path.exists() and not args.force:
        raise SystemExit(f"model already exists: {path}")
    payload = base_model(args)
    save_model(path, payload)
    print(path)


def cmd_validate(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = read_json(path)
    errors, warnings = validate_model(payload)
    for warning in warnings:
        print(f"warning: {warning}")
    if errors or (args.strict and warnings):
        for error in errors:
            print(f"error: {error}")
        raise SystemExit(1)
    index_model(path, payload)
    print(f"validated {path}")


def cmd_add_entity(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = load_model_for_write(path)
    items = collection(payload, "entities")
    item = common_assertion(args, args.entity_id or next_id(items, "entities"))
    item.update(
        {
            "kind": args.kind,
            "name": args.name,
            "description": args.description,
        }
    )
    action = replace_or_append(items, item, replace=args.replace)
    save_model(path, payload)
    print(f"{action} {item['id']}")


def cmd_add_relation(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = load_model_for_write(path)
    items = collection(payload, "relations")
    item = common_assertion(args, args.relation_id or next_id(items, "relations"))
    predicate = args.predicate.strip().lower().replace(" ", "_")
    item.update(
        {
            "subject": args.subject,
            "predicate": predicate,
            "object": args.object,
            "statement": args.statement or f"{args.subject} {predicate} {args.object}",
            "description": args.description,
        }
    )
    action = replace_or_append(items, item, replace=args.replace)
    save_model(path, payload)
    print(f"{action} {item['id']}")


def cmd_add_invariant(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = load_model_for_write(path)
    items = collection(payload, "invariants")
    item = common_assertion(args, args.invariant_id or next_id(items, "invariants"))
    item.update(
        {
            "statement": args.statement,
            "scope": args.scope,
            "formula": args.formula or "",
            "protected_asset": args.protected_asset or "",
            "actor": args.actor or "",
            "operation": args.operation or "",
            "object": args.object or "",
            "preconditions": parse_repeated(args.precondition),
            "violated_by": parse_repeated(args.violated_by),
        }
    )
    action = replace_or_append(items, item, replace=args.replace)
    save_model(path, payload)
    print(f"{action} {item['id']}")


def cmd_add_formula(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = load_model_for_write(path)
    items = collection(payload, "formulas")
    item = common_assertion(args, args.formula_id or next_id(items, "formulas"))
    item.update(
        {
            "formula": args.formula,
            "description": args.description,
            "scope": args.scope or "",
            "derived_from": parse_repeated(args.derived_from),
        }
    )
    action = replace_or_append(items, item, replace=args.replace)
    save_model(path, payload)
    print(f"{action} {item['id']}")


def cmd_add_assumption(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = load_model_for_write(path)
    items = collection(payload, "assumptions")
    item = common_assertion(args, args.assumption_id or next_id(items, "assumptions"))
    item.update({"statement": args.statement, "scope": args.scope})
    action = replace_or_append(items, item, replace=args.replace)
    save_model(path, payload)
    print(f"{action} {item['id']}")


def cmd_add_unknown(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = load_model_for_write(path)
    items = collection(payload, "unknowns")
    item = {
        "id": args.unknown_id or next_id(items, "unknowns"),
        "question": args.question,
        "scope": args.scope,
        "status": args.status,
        "evidence": parse_repeated(args.evidence),
        "owner": args.owner or "",
        "blocked_by": parse_repeated(args.blocked_by),
        "tags": parse_repeated(args.tag),
        "properties": parse_key_values(args.property),
    }
    action = replace_or_append(items, item, replace=args.replace)
    save_model(path, payload)
    print(f"{action} {item['id']}")


def cmd_add_contradiction(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = load_model_for_write(path)
    items = collection(payload, "contradictions")
    item = {
        "id": args.contradiction_id or next_id(items, "contradictions"),
        "statement": args.statement,
        "status": args.status,
        "assertion_refs": parse_repeated(args.assertion_ref),
        "evidence": parse_repeated(args.evidence),
        "resolution": args.resolution or "",
        "tags": parse_repeated(args.tag),
        "properties": parse_key_values(args.property),
    }
    action = replace_or_append(items, item, replace=args.replace)
    save_model(path, payload)
    print(f"{action} {item['id']}")


def text_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(text_values(item))
        return result
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(text_values(item))
        return result
    return [str(value)]


def tokens(value: str) -> set[str]:
    return {part for part in re.split(r"[^a-zA-Z0-9_+-]+", value.lower()) if len(part) > 2}


def assertion_text(item: dict[str, Any]) -> str:
    return " ".join(text_values(item))


def local_search(payload: dict[str, Any], query: str, limit: int) -> list[tuple[int, str, str, str]]:
    wanted = tokens(query)
    if not wanted:
        return []
    results: list[tuple[int, str, str, str]] = []
    for name in COLLECTIONS:
        for item in payload.get(name) or []:
            if not isinstance(item, dict):
                continue
            text = assertion_text(item)
            overlap = wanted & tokens(text)
            if overlap:
                results.append((len(overlap), name, str(item.get("id", "")), summarize_item(name, item)))
    results.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
    return results[: max(1, limit)]


def cmd_search(args: argparse.Namespace) -> None:
    if args.model_json:
        payload = read_json(Path(args.model_json))
        for score, collection_name, item_id, summary in local_search(payload, args.query, args.limit):
            print(f"score={score} {collection_name}:{item_id} {summary}")
        return
    if workspace_db is None or not hasattr(workspace_db, "search_models"):
        raise SystemExit("workspace_db model search is not available")
    root = Path(args.root).expanduser().resolve()
    results = workspace_db.search_models(root, args.query, args.limit)
    if not results:
        print("No model matches.")
        return
    for score, model_id, assertion_type, item_id, statement in results:
        item = f"{assertion_type}:{item_id}" if item_id else "model"
        print(f"score={score} {model_id} {item} {statement}")


def summarize_item(collection_name: str, item: dict[str, Any]) -> str:
    if collection_name == "entities":
        return f"{item.get('kind', '')} {item.get('name', '')}: {item.get('description', '')}".strip()
    if collection_name == "relations":
        return str(item.get("statement") or f"{item.get('subject')} {item.get('predicate')} {item.get('object')}")
    if collection_name == "invariants":
        return str(item.get("statement", ""))
    if collection_name == "formulas":
        return str(item.get("formula", ""))
    if collection_name == "assumptions":
        return str(item.get("statement", ""))
    if collection_name == "unknowns":
        return str(item.get("question", ""))
    if collection_name == "contradictions":
        return str(item.get("statement", ""))
    return assertion_text(item)


def evidence_text(values: list[str]) -> str:
    values = [value for value in values if str(value).strip()]
    return ", ".join(f"`{value}`" for value in values) if values else ""


def render_invariants(payload: dict[str, Any]) -> str:
    lines = [
        f"# Invariant Dictionary: {payload['model_id']}",
        "",
        f"- Target: {payload['target']['name']}",
        f"- Kind: {payload['target']['kind']}",
        f"- Updated: {payload.get('updated_at', '')}",
        "",
    ]
    invariants = payload.get("invariants") or []
    if not invariants:
        lines.append("No invariants recorded.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(["| ID | Status | Confidence | Scope | Invariant | Evidence |", "| --- | --- | --- | --- | --- | --- |"])
    for item in invariants:
        formula = f"<br>`{item.get('formula')}`" if item.get("formula") else ""
        statement = str(item.get("statement", "")).replace("|", "\\|")
        scope = str(item.get("scope", "")).replace("|", "\\|")
        lines.append(
            f"| `{item.get('id')}` | `{item.get('status')}` | `{item.get('confidence')}` | "
            f"{scope} | {statement}{formula} | {evidence_text(item.get('evidence') or [])} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_obligations(payload: dict[str, Any]) -> str:
    lines = [
        f"# Model Obligations: {payload['model_id']}",
        "",
        "## Unknowns",
        "",
    ]
    unknowns = payload.get("unknowns") or []
    if not unknowns:
        lines.append("No unknowns recorded.")
    for item in unknowns:
        lines.append(f"- `{item.get('id')}` `{item.get('status')}` {item.get('question')} ({item.get('scope')})")
        if item.get("blocked_by"):
            lines.append(f"  Blocked by: {', '.join(item.get('blocked_by') or [])}")
        if item.get("evidence"):
            lines.append(f"  Evidence: {evidence_text(item.get('evidence') or [])}")
    lines.extend(["", "## Assumptions", ""])
    assumptions = payload.get("assumptions") or []
    if not assumptions:
        lines.append("No assumptions recorded.")
    for item in assumptions:
        lines.append(
            f"- `{item.get('id')}` `{item.get('status')}` `{item.get('confidence')}` "
            f"{item.get('statement')} ({item.get('scope')})"
        )
        if item.get("evidence"):
            lines.append(f"  Evidence: {evidence_text(item.get('evidence') or [])}")
    lines.extend(["", "## Contradictions", ""])
    contradictions = payload.get("contradictions") or []
    if not contradictions:
        lines.append("No contradictions recorded.")
    for item in contradictions:
        refs = ", ".join(item.get("assertion_refs") or [])
        suffix = f" Refs: {refs}." if refs else ""
        resolution = f" Resolution: {item.get('resolution')}." if item.get("resolution") else ""
        lines.append(f"- `{item.get('id')}` `{item.get('status')}` {item.get('statement')}.{suffix}{resolution}")
    lines.append("")
    return "\n".join(lines)


def mermaid_id(value: str, used: set[str]) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip()) or "node"
    if base[0].isdigit():
        base = "n_" + base
    candidate = base
    counter = 2
    while candidate in used:
        candidate = f"{base}_{counter}"
        counter += 1
    used.add(candidate)
    return candidate


def mermaid_label(value: str) -> str:
    return str(value).replace('"', "'").replace("\n", " ")


def render_graph(payload: dict[str, Any]) -> str:
    used: set[str] = set()
    node_ids: dict[str, str] = {}
    lines = ["graph TD"]
    for entity in payload.get("entities") or []:
        entity_id = str(entity.get("id", ""))
        node = mermaid_id(entity_id, used)
        node_ids[entity_id] = node
        label = f"{entity_id}: {entity.get('name', '')}\\n{entity.get('kind', '')}"
        lines.append(f'  {node}["{mermaid_label(label)}"]')
    for relation in payload.get("relations") or []:
        subject = str(relation.get("subject", ""))
        obj = str(relation.get("object", ""))
        if subject not in node_ids or obj not in node_ids:
            continue
        predicate = mermaid_label(relation.get("predicate", "relates_to"))
        lines.append(f"  {node_ids[subject]} -->|{predicate}| {node_ids[obj]}")
    if len(lines) == 1:
        lines.append('  empty["No entities recorded"]')
    return "\n".join(lines) + "\n"


def cmd_project(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = read_json(path)
    errors, warnings = validate_model(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    output_dir = Path(args.output_dir) if args.output_dir else path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    invariants = output_dir / "invariants.md"
    obligations = output_dir / "obligations.md"
    graph = output_dir / "graph.mmd"
    invariants.write_text(render_invariants(payload), encoding="utf-8")
    obligations.write_text(render_obligations(payload), encoding="utf-8")
    graph.write_text(render_graph(payload), encoding="utf-8")
    index_model(path, payload)
    print(invariants)
    print(obligations)
    print(graph)


def render_prompt(payload: dict[str, Any], focus: str | None) -> str:
    target = payload["target"]
    lines = [
        "# MaxTAC Model-Backed Auditor Prompt",
        "",
        f"- Model: `{payload['model_id']}`",
        f"- Target: {target['name']} (`{target['kind']}`)",
        f"- Revision: {target.get('revision') or 'unknown'}",
    ]
    if focus:
        lines.append(f"- Focus: {focus}")
    lines.extend(
        [
            "",
            "## Ground Rules",
            "",
            "- Treat model assertions as context, not as proof of a finding.",
            "- Reconfirm candidate, stale, and low-confidence assertions before relying on them.",
            "- Separate facts, assumptions, unknowns, contradictions, and vulnerability conclusions.",
            "- Return updates that can be merged into the model with assertion IDs when possible.",
            "",
            "## Confirmed Or Observed Invariants",
            "",
        ]
    )
    invariant_rows = [
        item for item in payload.get("invariants") or [] if item.get("status") in {"observed", "confirmed"}
    ]
    if not invariant_rows:
        lines.append("- None recorded.")
    for item in invariant_rows:
        lines.append(f"- `{item.get('id')}` `{item.get('status')}` `{item.get('confidence')}` {item.get('statement')}")
        if item.get("formula"):
            lines.append(f"  Formula: `{item.get('formula')}`")
    lines.extend(["", "## Candidate Or Stale Assertions", ""])
    candidate_count = 0
    for name in ("relations", "invariants", "formulas", "assumptions"):
        for item in payload.get(name) or []:
            if item.get("status") in {"candidate", "stale"}:
                candidate_count += 1
                lines.append(
                    f"- `{name}:{item.get('id')}` `{item.get('status')}` `{item.get('confidence', 'unknown')}` "
                    f"{summarize_item(name, item)}"
                )
    if not candidate_count:
        lines.append("- None recorded.")
    lines.extend(["", "## Unknowns", ""])
    unknowns = payload.get("unknowns") or []
    if not unknowns:
        lines.append("- None recorded.")
    for item in unknowns:
        lines.append(f"- `{item.get('id')}` `{item.get('status')}` {item.get('question')} ({item.get('scope')})")
    lines.extend(["", "## Contradictions", ""])
    contradictions = payload.get("contradictions") or []
    if not contradictions:
        lines.append("- None recorded.")
    for item in contradictions:
        refs = ", ".join(item.get("assertion_refs") or [])
        suffix = f" Refs: {refs}." if refs else ""
        lines.append(f"- `{item.get('id')}` `{item.get('status')}` {item.get('statement')}.{suffix}")
    lines.extend(
        [
            "",
            "## Auditor Task",
            "",
            "1. Confirm, refute, narrow, or mark stale the model assertions relevant to the focus.",
            "2. Identify any violated invariant that could seed a MaxTAC finding hypothesis.",
            "3. Name missing evidence, unreachable paths, guard dominance, and false assumptions.",
            "4. Return concise model updates plus any recommended ledger, research, CFG, OpenGrep, RE, DAST, or proof action.",
            "",
            "## Required Response Shape",
            "",
            "- Assertions reviewed:",
            "- Confirmed model updates:",
            "- Refuted or stale assertions:",
            "- Unknowns resolved or newly created:",
            "- Potential invariant violations:",
            "- Evidence references:",
            "- Recommended next action:",
            "",
        ]
    )
    return "\n".join(lines)


def output_text(path: str | None, text: str) -> None:
    if not path or path == "-":
        print(text, end="")
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def cmd_export_prompt(args: argparse.Namespace) -> None:
    path = Path(args.model_json)
    payload = read_json(path)
    errors, warnings = validate_model(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    output_text(args.output, render_prompt(payload, args.focus))
    index_model(path, payload)


def cmd_summary(args: argparse.Namespace) -> None:
    payload = read_json(Path(args.model_json))
    errors, warnings = validate_model(payload)
    if errors:
        raise SystemExit("\n".join(errors))
    target = payload["target"]
    print(f"Model {payload['model_id']}: {target['name']} ({target['kind']})")
    for name in COLLECTIONS:
        items = payload.get(name) or []
        counts: dict[str, int] = {}
        for item in items:
            status = str(item.get("status", "unknown"))
            counts[status] = counts.get(status, 0) + 1
        summary = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
        print(f"- {name}: {len(items)}{f' ({summary})' if summary else ''}")
    for warning in warnings:
        print(f"- warning: {warning}")


def add_common_args(parser: argparse.ArgumentParser, *, confidence: bool = True) -> None:
    parser.add_argument("--status", choices=STATUSES, default="candidate")
    if confidence:
        parser.add_argument("--confidence", choices=CONFIDENCES, default="unknown")
    parser.add_argument("--evidence", action="append")
    parser.add_argument("--tag", action="append")
    parser.add_argument("--property", action="append", metavar="KEY=VALUE")
    parser.add_argument("--replace", action="store_true")


def add_init_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--kind", default="subsystem")
    parser.add_argument("--revision")
    parser.add_argument("--source")
    parser.add_argument("--summary")
    parser.add_argument("--include", action="append")
    parser.add_argument("--exclude", action="append")
    parser.add_argument("--limitation", action="append")
    parser.add_argument("--force", action="store_true")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC security model helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a canonical security model")
    add_init_args(init)
    init.set_defaults(func=cmd_init)

    validate = subparsers.add_parser("validate", help="Validate and index a model")
    validate.add_argument("model_json")
    validate.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    validate.set_defaults(func=cmd_validate)

    summary = subparsers.add_parser("summary", help="Summarize model assertion counts")
    summary.add_argument("model_json")
    summary.set_defaults(func=cmd_summary)

    entity = subparsers.add_parser("add-entity", help="Add or replace an entity")
    entity.add_argument("model_json")
    entity.add_argument("--entity-id")
    entity.add_argument("--kind", choices=ENTITY_KINDS, required=True)
    entity.add_argument("--name", required=True)
    entity.add_argument("--description", required=True)
    add_common_args(entity)
    entity.set_defaults(func=cmd_add_entity)

    relation = subparsers.add_parser("add-relation", help="Add or replace a relation")
    relation.add_argument("model_json")
    relation.add_argument("--relation-id")
    relation.add_argument("--subject", required=True)
    relation.add_argument("--predicate", required=True)
    relation.add_argument("--object", required=True)
    relation.add_argument("--statement")
    relation.add_argument("--description", required=True)
    add_common_args(relation)
    relation.set_defaults(func=cmd_add_relation)

    invariant = subparsers.add_parser("add-invariant", help="Add or replace an invariant")
    invariant.add_argument("model_json")
    invariant.add_argument("--invariant-id")
    invariant.add_argument("--statement", required=True)
    invariant.add_argument("--scope", required=True)
    invariant.add_argument("--formula")
    invariant.add_argument("--protected-asset")
    invariant.add_argument("--actor")
    invariant.add_argument("--operation")
    invariant.add_argument("--object")
    invariant.add_argument("--precondition", action="append")
    invariant.add_argument("--violated-by", action="append")
    add_common_args(invariant)
    invariant.set_defaults(func=cmd_add_invariant)

    formula = subparsers.add_parser("add-formula", help="Add or replace a first-order-logic-style formula")
    formula.add_argument("model_json")
    formula.add_argument("--formula-id")
    formula.add_argument("--formula", required=True)
    formula.add_argument("--description", required=True)
    formula.add_argument("--scope")
    formula.add_argument("--derived-from", action="append")
    add_common_args(formula)
    formula.set_defaults(func=cmd_add_formula)

    assumption = subparsers.add_parser("add-assumption", help="Add or replace an assumption")
    assumption.add_argument("model_json")
    assumption.add_argument("--assumption-id")
    assumption.add_argument("--statement", required=True)
    assumption.add_argument("--scope", required=True)
    add_common_args(assumption)
    assumption.set_defaults(func=cmd_add_assumption)

    unknown = subparsers.add_parser("add-unknown", help="Add or replace an unknown or proof obligation")
    unknown.add_argument("model_json")
    unknown.add_argument("--unknown-id")
    unknown.add_argument("--question", required=True)
    unknown.add_argument("--scope", required=True)
    unknown.add_argument("--owner")
    unknown.add_argument("--blocked-by", action="append")
    add_common_args(unknown, confidence=False)
    unknown.set_defaults(func=cmd_add_unknown)

    contradiction = subparsers.add_parser("add-contradiction", help="Add or replace a contradiction")
    contradiction.add_argument("model_json")
    contradiction.add_argument("--contradiction-id")
    contradiction.add_argument("--statement", required=True)
    contradiction.add_argument("--assertion-ref", action="append", required=True)
    contradiction.add_argument("--resolution")
    add_common_args(contradiction, confidence=False)
    contradiction.set_defaults(func=cmd_add_contradiction)

    project = subparsers.add_parser("project", help="Project invariants.md, obligations.md, and graph.mmd")
    project.add_argument("model_json")
    project.add_argument("--output-dir")
    project.set_defaults(func=cmd_project)

    search = subparsers.add_parser("search", help="Search a model file or indexed workspace models")
    search.add_argument("model_json", nargs="?")
    search.add_argument("--root", default=".")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=10)
    search.set_defaults(func=cmd_search)

    export_prompt = subparsers.add_parser("export-prompt", help="Export a model-backed auditor prompt")
    export_prompt.add_argument("model_json")
    export_prompt.add_argument("--focus")
    export_prompt.add_argument("--output")
    export_prompt.set_defaults(func=cmd_export_prompt)

    return parser


def main() -> None:
    parser = base_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
