#!/usr/bin/env python3
"""SQLite-backed MaxTAC auditor registry.

The registry is rebuilt at Codex session start from active MaxTAC plugin packs.
It is global to the Codex installation because auditor availability is a plugin
property, not a per-research-workspace finding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback.
    tomllib = None  # type: ignore[assignment]


DB_FILE = "auditors.sqlite"
SCHEMA_VERSION = "1"
CATALOG_ALIASES = {
    "fallback": "core",
    "apple-systems": "apple",
    "microsoft-systems": "microsoft",
    "windows": "microsoft",
    "supply": "supply-chain",
    "supply-chain": "supply-chain",
    "supply-chains": "supply-chain",
    "supply_chain": "supply-chain",
    "supplychains": "supply-chain",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()


def default_db_path() -> Path:
    override = os.environ.get("MAXTAC_AUDITOR_DB")
    if override:
        return Path(override).expanduser()
    return codex_home() / "maxtac" / DB_FILE


def plugin_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = (db_path or default_db_path()).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def ensure_schema(conn: sqlite3.Connection) -> bool:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS auditors (
          auditor_key TEXT PRIMARY KEY,
          dedupe_key TEXT NOT NULL UNIQUE,
          catalog TEXT NOT NULL,
          auditor_id TEXT NOT NULL,
          plugin_name TEXT NOT NULL,
          plugin_version TEXT NOT NULL,
          plugin_root TEXT NOT NULL,
          source_path TEXT NOT NULL,
          name TEXT NOT NULL,
          topic TEXT NOT NULL DEFAULT '',
          category TEXT NOT NULL DEFAULT '',
          specialty TEXT NOT NULL DEFAULT '',
          summary TEXT NOT NULL DEFAULT '',
          tags_json TEXT NOT NULL DEFAULT '[]',
          markdown TEXT NOT NULL DEFAULT '',
          search_text TEXT NOT NULL,
          raw_json TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE(catalog, auditor_id)
        );

        CREATE INDEX IF NOT EXISTS idx_auditors_catalog ON auditors(catalog);
        CREATE INDEX IF NOT EXISTS idx_auditors_plugin ON auditors(plugin_name);
        """
    )
    set_meta(conn, "schema_version", SCHEMA_VERSION)
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS auditor_search USING fts5("
            "auditor_key UNINDEXED, catalog UNINDEXED, text, tokenize='porter unicode61')"
        )
    except sqlite3.DatabaseError:
        set_meta(conn, "fts5_enabled", "0")
        conn.commit()
        return False
    set_meta(conn, "fts5_enabled", "1")
    conn.commit()
    return True


def fts5_enabled(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT value FROM meta WHERE key = 'fts5_enabled'").fetchone()
    return bool(row and row["value"] == "1")


def normalize_catalog(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.strip().lower().replace("_", "-")
    return CATALOG_ALIASES.get(key, key)


def catalog_for_plugin(plugin_name: str) -> str:
    name = plugin_name.removeprefix("maxtac-")
    return normalize_catalog(name) or name


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_for(root: Path) -> dict[str, Any] | None:
    path = root / ".codex-plugin" / "plugin.json"
    if not path.exists():
        return None
    try:
        payload = load_json(path)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def enabled_plugin_names(config_path: Path | None = None) -> set[str]:
    path = config_path or (codex_home() / "config.toml")
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        try:
            payload = tomllib.loads(text)
        except Exception:
            payload = {}
        plugins = payload.get("plugins") if isinstance(payload, dict) else None
        if isinstance(plugins, dict):
            result: set[str] = set()
            for key, value in plugins.items():
                if isinstance(value, dict) and value.get("enabled") is True:
                    result.add(str(key).split("@", 1)[0])
            return result

    result: set[str] = set()
    current_plugin: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.match(r'^\[plugins\."([^"]+)"\]$', line)
        if match:
            current_plugin = match.group(1).split("@", 1)[0]
            continue
        if current_plugin and line == "enabled = true":
            result.add(current_plugin)
    return result


def latest_plugin_roots(cache_local: Path) -> list[Path]:
    roots: list[Path] = []
    for plugin_dir in sorted(cache_local.glob("maxtac-*")):
        if not plugin_dir.is_dir():
            continue
        candidates = [
            child
            for child in plugin_dir.iterdir()
            if child.is_dir() and (child / ".codex-plugin" / "plugin.json").exists()
        ]
        if candidates:
            roots.append(max(candidates, key=lambda item: item.stat().st_mtime))
    return roots


def discover_plugin_roots(start_root: Path | None = None) -> list[Path]:
    core_root = start_root or plugin_root_from_script()

    # Installed cache layout: ~/.codex/plugins/cache/local/<plugin>/<version>/
    if core_root.parent.name.startswith("maxtac-") and core_root.parent.parent.name == "local":
        return latest_plugin_roots(core_root.parent.parent)

    # Source layout: <repo>/plugins/<plugin>/
    sibling_roots = [
        child
        for child in sorted(core_root.parent.glob("maxtac-*"))
        if child.is_dir() and (child / ".codex-plugin" / "plugin.json").exists()
    ]
    if sibling_roots:
        return sibling_roots

    cache_local = codex_home() / "plugins" / "cache" / "local"
    if cache_local.exists():
        return latest_plugin_roots(cache_local)
    return [core_root]


def catalog_paths_for_plugin(root: Path) -> list[Path]:
    return [
        root / "references" / "auditors.json",
        root / "skills" / "maxtac-core-subagents" / "references" / "auditors.json",
    ]


def list_item_id(index: int, item: Any) -> str:
    if isinstance(item, dict) and item.get("id"):
        return str(item["id"])
    return f"auditor-{index + 1}"


def normalize_auditor(auditor_id: str, auditor: Any) -> dict[str, Any]:
    if isinstance(auditor, str):
        return {"id": auditor_id, "name": auditor_id, "markdown": auditor}
    if not isinstance(auditor, dict):
        raise ValueError(f"Auditor {auditor_id} must be an object or markdown string")
    result = dict(auditor)
    result.setdefault("id", auditor_id)
    result.setdefault("name", result["id"])
    return result


def auditors_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("auditors"), list):
        return [
            normalize_auditor(list_item_id(index, item), item)
            for index, item in enumerate(payload["auditors"])
        ]
    if isinstance(payload, dict):
        return [normalize_auditor(str(key), value) for key, value in payload.items()]
    if isinstance(payload, list):
        return [
            normalize_auditor(list_item_id(index, item), item)
            for index, item in enumerate(payload)
        ]
    raise ValueError("Auditor catalog must be a JSON list or object")


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


def markdown_for(auditor: dict[str, Any]) -> str:
    value = auditor.get("markdown")
    if isinstance(value, str):
        return value.strip() + "\n"
    if isinstance(value, list):
        return "\n".join(str(line) for line in value).strip() + "\n"
    for key in ("instructions", "prompt", "content"):
        value = auditor.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip() + "\n"
        if isinstance(value, list) and value:
            return "\n".join(str(line) for line in value).strip() + "\n"
    return f"# {auditor.get('name')}\n\n- Auditor: {auditor.get('id')}\n- Summary: {auditor.get('summary', '')}\n"


def search_blob(record: dict[str, Any]) -> str:
    return " ".join(part for value in record.values() for part in text_values(value))


def stable_key(catalog: str, auditor_id: str) -> str:
    return f"{catalog}:{auditor_id}"


def dedupe_key(catalog: str, auditor_id: str, auditor: dict[str, Any]) -> str:
    material = json.dumps(
        {
            "catalog": catalog,
            "id": auditor_id,
            "name": auditor.get("name"),
            "summary": auditor.get("summary"),
        },
        sort_keys=True,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def collect_auditors(*, active_only: bool = True) -> tuple[list[dict[str, Any]], list[str]]:
    enabled = enabled_plugin_names() if active_only else set()
    rows: list[dict[str, Any]] = []
    loaded_plugins: list[str] = []
    seen_keys: set[str] = set()

    for root in discover_plugin_roots():
        manifest = manifest_for(root)
        if not manifest:
            continue
        plugin_name = str(manifest.get("name") or root.name)
        if active_only and enabled and plugin_name not in enabled:
            continue
        plugin_version = str(manifest.get("version") or "")
        catalog = catalog_for_plugin(plugin_name)
        plugin_loaded = False
        for catalog_path in catalog_paths_for_plugin(root):
            if not catalog_path.exists():
                continue
            payload = load_json(catalog_path)
            for auditor in auditors_from_payload(payload):
                auditor_id = str(auditor.get("id") or "").strip()
                if not auditor_id:
                    continue
                auditor_key = stable_key(catalog, auditor_id)
                if auditor_key in seen_keys:
                    continue
                seen_keys.add(auditor_key)
                raw_json = json.dumps(auditor, sort_keys=True)
                tags = auditor.get("tags") or auditor.get("keywords") or []
                if not isinstance(tags, list):
                    tags = [str(tags)]
                row = {
                    "auditor_key": auditor_key,
                    "dedupe_key": dedupe_key(catalog, auditor_id, auditor),
                    "catalog": catalog,
                    "auditor_id": auditor_id,
                    "plugin_name": plugin_name,
                    "plugin_version": plugin_version,
                    "plugin_root": str(root),
                    "source_path": str(catalog_path),
                    "name": str(auditor.get("name") or auditor_id),
                    "topic": str(auditor.get("topic") or ""),
                    "category": str(auditor.get("category") or ""),
                    "specialty": str(auditor.get("specialty") or auditor.get("focus") or ""),
                    "summary": str(auditor.get("summary") or auditor.get("description") or ""),
                    "tags_json": json.dumps(tags),
                    "markdown": markdown_for(auditor),
                    "search_text": search_blob(auditor),
                    "raw_json": raw_json,
                    "updated_at": utc_now(),
                }
                rows.append(row)
                plugin_loaded = True
        if plugin_loaded:
            loaded_plugins.append(f"{plugin_name}@{plugin_version}")

    rows.sort(key=lambda item: (item["catalog"], item["auditor_id"]))
    return rows, loaded_plugins


def rebuild_registry(db_path: Path | None = None, *, active_only: bool = True) -> dict[str, Any]:
    path = db_path or default_db_path()
    auditors, loaded_plugins = collect_auditors(active_only=active_only)
    with connect(path) as conn:
        ensure_schema(conn)
        conn.execute("DELETE FROM auditor_search")
        conn.execute("DELETE FROM auditors")
        for auditor in auditors:
            conn.execute(
                """
                INSERT INTO auditors(
                  auditor_key, dedupe_key, catalog, auditor_id, plugin_name,
                  plugin_version, plugin_root, source_path, name, topic,
                  category, specialty, summary, tags_json, markdown,
                  search_text, raw_json, updated_at
                ) VALUES (
                  :auditor_key, :dedupe_key, :catalog, :auditor_id, :plugin_name,
                  :plugin_version, :plugin_root, :source_path, :name, :topic,
                  :category, :specialty, :summary, :tags_json, :markdown,
                  :search_text, :raw_json, :updated_at
                )
                """,
                auditor,
            )
            if fts5_enabled(conn):
                conn.execute(
                    "INSERT INTO auditor_search(auditor_key, catalog, text) VALUES (?, ?, ?)",
                    (auditor["auditor_key"], auditor["catalog"], auditor["search_text"]),
                )
        set_meta(conn, "last_rebuilt_at", utc_now())
        set_meta(conn, "last_rebuild_active_only", "1" if active_only else "0")
        set_meta(conn, "loaded_plugins_json", json.dumps(loaded_plugins))
        conn.commit()
    counts: dict[str, int] = {}
    for auditor in auditors:
        counts[auditor["catalog"]] = counts.get(auditor["catalog"], 0) + 1
    return {
        "db": str(path),
        "active_only": active_only,
        "count": len(auditors),
        "catalogs": counts,
        "plugins": loaded_plugins,
    }


def auditor_count(db_path: Path | None = None) -> int:
    with connect(db_path) as conn:
        ensure_schema(conn)
        row = conn.execute("SELECT COUNT(*) AS count FROM auditors").fetchone()
        return int(row["count"])


def ensure_ready(db_path: Path | None = None) -> None:
    if auditor_count(db_path) == 0:
        rebuild_registry(db_path, active_only=True)


def row_to_auditor(row: sqlite3.Row) -> dict[str, Any]:
    payload = json.loads(row["raw_json"])
    if isinstance(payload, dict):
        payload.setdefault("id", row["auditor_id"])
        payload.setdefault("name", row["name"])
        payload["_registry"] = {
            "catalog": row["catalog"],
            "plugin_name": row["plugin_name"],
            "plugin_version": row["plugin_version"],
            "source_path": row["source_path"],
        }
        return payload
    return {
        "id": row["auditor_id"],
        "name": row["name"],
        "summary": row["summary"],
        "markdown": row["markdown"],
        "_registry": {"catalog": row["catalog"]},
    }


def list_catalog_counts(db_path: Path | None = None) -> list[tuple[str, int]]:
    ensure_ready(db_path)
    with connect(db_path) as conn:
        ensure_schema(conn)
        rows = conn.execute(
            "SELECT catalog, COUNT(*) AS count FROM auditors GROUP BY catalog ORDER BY catalog"
        ).fetchall()
    return [(str(row["catalog"]), int(row["count"])) for row in rows]


def list_auditors(db_path: Path | None = None, *, catalog: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    ensure_ready(db_path)
    normalized = normalize_catalog(catalog)
    with connect(db_path) as conn:
        ensure_schema(conn)
        params: list[Any] = []
        where = ""
        if normalized:
            where = "WHERE catalog = ?"
            params.append(normalized)
        sql = f"SELECT * FROM auditors {where} ORDER BY catalog, auditor_id"
        if limit:
            sql += " LIMIT ?"
            params.append(max(1, limit))
        rows = conn.execute(sql, params).fetchall()
    return [row_to_auditor(row) for row in rows]


def token_set(*values: Any) -> set[str]:
    text = " ".join(str(value or "") for value in values)
    return {part for part in re.split(r"[^a-zA-Z0-9_+-]+", text.lower()) if len(part) > 2}


def fts_query(text: str) -> str:
    parts = sorted(token_set(text))
    return " OR ".join(f'"{part.replace(chr(34), chr(34) + chr(34))}"' for part in parts)


def filter_auditors(
    db_path: Path | None,
    query: str,
    *,
    catalog: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    ensure_ready(db_path)
    normalized = normalize_catalog(catalog)
    query_text = fts_query(query)
    if not query_text:
        return []
    limit = max(1, limit)
    with connect(db_path) as conn:
        ensure_schema(conn)
        if fts5_enabled(conn):
            params: list[Any] = [query_text]
            where = "auditor_search MATCH ?"
            if normalized:
                where += " AND auditor_search.catalog = ?"
                params.append(normalized)
            params.append(limit)
            rows = conn.execute(
                "SELECT auditors.* FROM auditor_search "
                "JOIN auditors USING(auditor_key) "
                f"WHERE {where} ORDER BY bm25(auditor_search) ASC LIMIT ?",
                params,
            ).fetchall()
            return [row_to_auditor(row) for row in rows]
        rows = list_auditors(db_path, catalog=normalized)
    wanted = token_set(query)
    matches = [
        auditor
        for auditor in rows
        if wanted & token_set(search_blob(auditor))
    ]
    return matches[:limit]


def show_auditor(db_path: Path | None, auditor_id: str, *, catalog: str | None = None) -> dict[str, Any] | None:
    ensure_ready(db_path)
    normalized = normalize_catalog(catalog)
    with connect(db_path) as conn:
        ensure_schema(conn)
        params: list[Any] = [auditor_id.lower()]
        where = "lower(auditor_id) = ?"
        if normalized:
            where += " AND catalog = ?"
            params.append(normalized)
        rows = conn.execute(f"SELECT * FROM auditors WHERE {where} ORDER BY catalog", params).fetchall()
        if not rows:
            return None
        if len(rows) > 1 and not normalized:
            return {
                "id": auditor_id,
                "name": auditor_id,
                "summary": "Multiple auditors matched; specify --catalog.",
                "matches": [f"{row['catalog']}:{row['auditor_id']}" for row in rows],
            }
        return row_to_auditor(rows[0])


def condensed(auditor: dict[str, Any]) -> str:
    registry = auditor.get("_registry") if isinstance(auditor.get("_registry"), dict) else {}
    catalog = str(registry.get("catalog") or "")
    auditor_id = str(auditor.get("id", "")).strip()
    name = str(auditor.get("name") or auditor.get("title") or auditor_id).strip()
    specialty = auditor.get("specialty") or auditor.get("category") or auditor.get("focus")
    summary = auditor.get("summary") or auditor.get("description") or auditor.get("usage")
    tags = auditor.get("tags") or auditor.get("keywords") or auditor.get("cwe")
    parts = [f"- {catalog}:{auditor_id}: {name}" if catalog else f"- {auditor_id}: {name}"]
    if specialty:
        parts.append(f"specialty={specialty}")
    if tags:
        if isinstance(tags, list):
            tags = ", ".join(str(tag) for tag in tags)
        parts.append(f"tags={tags}")
    if summary:
        parts.append(str(summary))
    return " | ".join(parts)


def markdown_for_output(auditor: dict[str, Any]) -> str:
    matches = auditor.get("matches")
    if isinstance(matches, list):
        return "\n".join(["Multiple auditors matched. Specify --catalog:", *[f"- {item}" for item in matches]]) + "\n"
    return markdown_for(auditor)


def print_catalogs(db_path: Path | None = None) -> None:
    print(f"Auditor registry: {(db_path or default_db_path()).expanduser()}")
    for catalog, count in list_catalog_counts(db_path):
        print(f"- {catalog}: {count} auditor(s)")


def base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MaxTAC SQLite auditor registry")
    parser.add_argument("--db", type=Path, default=default_db_path(), help="Auditor registry SQLite path")
    sub = parser.add_subparsers(dest="command", required=True)

    rebuild = sub.add_parser("rebuild", help="Rebuild the registry from plugin catalogs")
    rebuild.add_argument("--active-only", action="store_true", default=True, help="Only load enabled plugins from Codex config")
    rebuild.add_argument("--all-installed", action="store_true", help="Load every discovered MaxTAC plugin catalog")
    rebuild.add_argument("--json", action="store_true", help="Print summary as JSON")
    rebuild.add_argument("--quiet", action="store_true", help="Suppress non-error output")

    sub.add_parser("catalogs", help="List catalog counts")

    list_cmd = sub.add_parser("list", help="List condensed auditors")
    list_cmd.add_argument("--catalog", help="Catalog to list")
    list_cmd.add_argument("--limit", type=int, help="Maximum rows")

    filter_cmd = sub.add_parser("filter", help="Search auditors")
    filter_cmd.add_argument("query")
    filter_cmd.add_argument("--catalog", help="Catalog to search")
    filter_cmd.add_argument("--limit", type=int, default=20)

    show_cmd = sub.add_parser("show", help="Show one auditor")
    show_cmd.add_argument("auditor_id")
    show_cmd.add_argument("--catalog", help="Catalog containing the auditor")

    sub.add_parser("path", help="Print the registry path")
    return parser


def main() -> None:
    args = base_parser().parse_args()
    db_path = args.db.expanduser()
    if args.command == "rebuild":
        summary = rebuild_registry(db_path, active_only=not args.all_installed)
        if args.quiet:
            return
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
            return
        print(f"Rebuilt {summary['count']} auditor(s) into {summary['db']}")
        for catalog, count in sorted(summary["catalogs"].items()):
            print(f"- {catalog}: {count}")
        return
    if args.command == "catalogs":
        print_catalogs(db_path)
        return
    if args.command == "list":
        for auditor in list_auditors(db_path, catalog=args.catalog, limit=args.limit):
            print(condensed(auditor))
        return
    if args.command == "filter":
        matches = filter_auditors(db_path, args.query, catalog=args.catalog, limit=args.limit)
        if not matches:
            print("No matching auditors.")
            return
        for auditor in matches:
            print(condensed(auditor))
        return
    if args.command == "show":
        auditor = show_auditor(db_path, args.auditor_id, catalog=args.catalog)
        if auditor is None:
            raise SystemExit(f"Auditor not found: {args.auditor_id}")
        print(markdown_for_output(auditor), end="")
        return
    if args.command == "path":
        print(db_path)
        return
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
