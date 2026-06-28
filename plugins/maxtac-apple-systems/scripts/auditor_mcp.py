#!/usr/bin/env python3
"""Small MCP server exposing a domain auditor catalog."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PREFIX = re.sub(r"[^a-z0-9_]+", "_", os.environ.get("MAXTAC_AUDITOR_PREFIX", "domain").lower()).strip("_") or "domain"
AUDITORS_FILE = PLUGIN_ROOT / os.environ.get("MAXTAC_AUDITORS_FILE", "references/auditors.json")


class ToolFailure(Exception):
    pass


def read_auditors() -> list[dict[str, Any]]:
    try:
        payload = json.loads(AUDITORS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ToolFailure(f"Auditor catalog not found: {AUDITORS_FILE}") from exc
    except json.JSONDecodeError as exc:
        raise ToolFailure(f"Auditor catalog is invalid JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise ToolFailure("Auditor catalog must be a JSON list")
    result = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ToolFailure(f"Auditor entry {index} must be an object")
        auditor = dict(item)
        auditor.setdefault("id", f"auditor-{index + 1}")
        auditor.setdefault("name", auditor["id"])
        result.append(auditor)
    return sorted(result, key=lambda item: str(item.get("id", "")))


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


def search_text(auditor: dict[str, Any]) -> str:
    return " ".join(text_values(auditor)).lower()


def condensed(auditor: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": auditor.get("id"),
        "name": auditor.get("name"),
        "category": auditor.get("category"),
        "specialty": auditor.get("specialty"),
        "tags": auditor.get("tags", []),
        "summary": auditor.get("summary"),
    }


def markdown_for(auditor: dict[str, Any]) -> str:
    value = auditor.get("markdown")
    if isinstance(value, str):
        return value.strip() + "\n"
    if isinstance(value, list):
        return "\n".join(str(line) for line in value).strip() + "\n"
    return f"# {auditor.get('name')}\n\n- Auditor: {auditor.get('id')}\n- Summary: {auditor.get('summary', '')}\n"


def tool_list(args: dict[str, Any]) -> dict[str, Any]:
    auditors = [condensed(item) for item in read_auditors()]
    return {"catalog": PREFIX, "count": len(auditors), "auditors": auditors}


def tool_filter(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query", "")).strip().lower()
    if not query:
        raise ToolFailure("Missing required field: query")
    limit = int(args.get("limit", 20))
    matches = [condensed(item) for item in read_auditors() if query in search_text(item)]
    return {"catalog": PREFIX, "query": query, "count": len(matches), "auditors": matches[:limit]}


def tool_show(args: dict[str, Any]) -> dict[str, Any]:
    auditor_id = str(args.get("auditor_id", "")).strip().lower()
    if not auditor_id:
        raise ToolFailure("Missing required field: auditor_id")
    for auditor in read_auditors():
        if str(auditor.get("id", "")).lower() == auditor_id:
            return {"catalog": PREFIX, "auditor": condensed(auditor), "markdown": markdown_for(auditor)}
    raise ToolFailure(f"Auditor not found: {auditor_id}")


def schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        payload["required"] = required
    return payload


TOOLS = {
    f"{PREFIX}_auditor_list": {
        "description": f"List condensed {PREFIX} MaxTAC auditors.",
        "inputSchema": schema({}),
        "handler": tool_list,
    },
    f"{PREFIX}_auditor_filter": {
        "description": f"Filter {PREFIX} MaxTAC auditors by text.",
        "inputSchema": schema({"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1}}, ["query"]),
        "handler": tool_filter,
    },
    f"{PREFIX}_auditor_show": {
        "description": f"Show full markdown instructions for one {PREFIX} MaxTAC auditor.",
        "inputSchema": schema({"auditor_id": {"type": "string"}}, ["auditor_id"]),
        "handler": tool_show,
    },
}


def response(message_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def tool_response(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {"isError": is_error, "content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}
    if method == "initialize":
        return response(message_id, {"protocolVersion": params.get("protocolVersion") or "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": f"maxtac-{PREFIX}-auditors", "version": "0.1.0"}})
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return response(message_id, {"tools": [{"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]} for name, spec in TOOLS.items()]})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name not in TOOLS:
            return response(message_id, tool_response({"error": f"Unknown tool: {name}"}, is_error=True))
        try:
            return response(message_id, tool_response(TOOLS[name]["handler"](arguments)))
        except Exception as exc:  # noqa: BLE001 - MCP tool errors should not crash the server.
            return response(message_id, tool_response({"error": str(exc)}, is_error=True))
    if method == "ping":
        return response(message_id, {})
    if message_id is not None:
        return {"jsonrpc": "2.0", "id": message_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return None


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            outgoing = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {exc}"}}
        else:
            outgoing = handle_request(message) if isinstance(message, dict) else {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
        if outgoing is not None:
            sys.stdout.write(json.dumps(outgoing, separators=(",", ":")) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
