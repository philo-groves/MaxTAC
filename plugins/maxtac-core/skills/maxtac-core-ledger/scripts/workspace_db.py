"""Shared SQLite storage for MaxTAC workspace findings."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DB_FILE = "workspace.sqlite"
LEGACY_LEDGER_FILES = {
    "primitive": Path("primitives.json"),
    "chain": Path("chains.json"),
}
TYPE_CHOICES = tuple(LEGACY_LEDGER_FILES)
SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class InitResult:
    created: bool
    imported: dict[str, int]
    fts5_enabled: bool


def db_path(root: Path) -> Path:
    return root / DB_FILE


def finding_key(finding_type: str, finding_id: str) -> str:
    return f"{finding_type}:{finding_id}"


def connect(root: Path) -> sqlite3.Connection:
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path(root))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def ensure_schema(conn: sqlite3.Connection) -> bool:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS findings (
          finding_key TEXT PRIMARY KEY,
          id TEXT NOT NULL,
          type TEXT NOT NULL CHECK (type IN ('primitive', 'chain')),
          title TEXT NOT NULL,
          target TEXT NOT NULL,
          category TEXT NOT NULL,
          summary TEXT NOT NULL,
          state TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          raw_json TEXT NOT NULL,
          UNIQUE(type, id)
        );

        CREATE INDEX IF NOT EXISTS idx_findings_type_state ON findings(type, state);
        CREATE INDEX IF NOT EXISTS idx_findings_updated ON findings(updated_at);

        CREATE TABLE IF NOT EXISTS finding_locations (
          finding_key TEXT NOT NULL,
          ordinal INTEGER NOT NULL,
          location TEXT NOT NULL,
          PRIMARY KEY (finding_key, ordinal),
          FOREIGN KEY (finding_key) REFERENCES findings(finding_key) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS finding_evidence (
          finding_key TEXT NOT NULL,
          ordinal INTEGER NOT NULL,
          evidence TEXT NOT NULL,
          PRIMARY KEY (finding_key, ordinal),
          FOREIGN KEY (finding_key) REFERENCES findings(finding_key) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS finding_related (
          finding_key TEXT NOT NULL,
          ordinal INTEGER NOT NULL,
          related_id TEXT NOT NULL,
          PRIMARY KEY (finding_key, ordinal),
          FOREIGN KEY (finding_key) REFERENCES findings(finding_key) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chain_primitives (
          chain_key TEXT NOT NULL,
          ordinal INTEGER NOT NULL,
          primitive_id TEXT NOT NULL,
          PRIMARY KEY (chain_key, ordinal),
          FOREIGN KEY (chain_key) REFERENCES findings(finding_key) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS finding_milestones (
          finding_key TEXT NOT NULL,
          ordinal INTEGER NOT NULL,
          time TEXT NOT NULL,
          note TEXT NOT NULL,
          PRIMARY KEY (finding_key, ordinal),
          FOREIGN KEY (finding_key) REFERENCES findings(finding_key) ON DELETE CASCADE
        );
        """
    )
    set_meta(conn, "schema_version", SCHEMA_VERSION)
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS finding_search USING fts5("
            "finding_key UNINDEXED, type UNINDEXED, text, tokenize='porter unicode61')"
        )
    except sqlite3.DatabaseError:
        set_meta(conn, "fts5_enabled", "0")
        conn.commit()
        return False
    set_meta(conn, "fts5_enabled", "1")
    conn.commit()
    return True


def fts5_enabled(conn: sqlite3.Connection) -> bool:
    return get_meta(conn, "fts5_enabled", "0") == "1"


def token_set(*values: Any) -> set[str]:
    text = " ".join(str(value or "") for value in values)
    return {part for part in re.split(r"[^a-zA-Z0-9_+-]+", text.lower()) if len(part) > 2}


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


def search_text(finding: dict[str, Any]) -> str:
    fields = [
        finding.get("id"),
        finding.get("type"),
        finding.get("title"),
        finding.get("target"),
        finding.get("category"),
        finding.get("summary"),
        finding.get("state"),
        finding.get("locations", []),
        finding.get("evidence", []),
        finding.get("related", []),
        finding.get("primitives", []),
        finding.get("milestones", []),
    ]
    return " ".join(part for value in fields for part in text_values(value))


def read_legacy_ledger(root: Path, finding_type: str) -> dict[str, Any] | None:
    path = root / LEGACY_LEDGER_FILES[finding_type]
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        raise SystemExit(f"{path} is not a MaxTAC findings ledger")
    payload.setdefault("version", 1)
    payload.setdefault("type", finding_type)
    return payload


def count_findings(root: Path, finding_type: str | None = None) -> int:
    with connect(root) as conn:
        ensure_schema(conn)
        if finding_type:
            row = conn.execute("SELECT COUNT(*) AS count FROM findings WHERE type = ?", (finding_type,)).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) AS count FROM findings").fetchone()
        return int(row["count"])


def replace_findings(conn: sqlite3.Connection, finding_type: str, findings: list[dict[str, Any]]) -> None:
    if finding_type not in TYPE_CHOICES:
        raise SystemExit(f"Unknown finding type: {finding_type}")
    if fts5_enabled(conn):
        conn.execute("DELETE FROM finding_search WHERE type = ?", (finding_type,))
    conn.execute("DELETE FROM findings WHERE type = ?", (finding_type,))

    for finding in findings:
        if not isinstance(finding, dict):
            continue
        finding = dict(finding)
        finding["type"] = finding_type
        finding_id = str(finding.get("id") or "").strip()
        if not finding_id:
            raise SystemExit(f"{finding_type} finding is missing id")
        key = finding_key(finding_type, finding_id)
        raw_json = json.dumps(finding, sort_keys=True)
        conn.execute(
            """
            INSERT INTO findings(
              finding_key, id, type, title, target, category, summary, state,
              created_at, updated_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                finding_id,
                finding_type,
                str(finding.get("title") or ""),
                str(finding.get("target") or ""),
                str(finding.get("category") or ""),
                str(finding.get("summary") or ""),
                str(finding.get("state") or "discovered"),
                str(finding.get("created_at") or ""),
                str(finding.get("updated_at") or ""),
                raw_json,
            ),
        )
        for ordinal, location in enumerate(finding.get("locations") or []):
            conn.execute(
                "INSERT INTO finding_locations(finding_key, ordinal, location) VALUES (?, ?, ?)",
                (key, ordinal, str(location)),
            )
        for ordinal, evidence in enumerate(finding.get("evidence") or []):
            conn.execute(
                "INSERT INTO finding_evidence(finding_key, ordinal, evidence) VALUES (?, ?, ?)",
                (key, ordinal, str(evidence)),
            )
        for ordinal, related in enumerate(finding.get("related") or []):
            conn.execute(
                "INSERT INTO finding_related(finding_key, ordinal, related_id) VALUES (?, ?, ?)",
                (key, ordinal, str(related)),
            )
        if finding_type == "chain":
            for ordinal, primitive_id in enumerate(finding.get("primitives") or []):
                conn.execute(
                    "INSERT INTO chain_primitives(chain_key, ordinal, primitive_id) VALUES (?, ?, ?)",
                    (key, ordinal, str(primitive_id)),
                )
        for ordinal, milestone in enumerate(finding.get("milestones") or []):
            if isinstance(milestone, dict):
                timestamp = str(milestone.get("time") or "")
                note = str(milestone.get("note") or "")
            else:
                timestamp = ""
                note = str(milestone)
            conn.execute(
                "INSERT INTO finding_milestones(finding_key, ordinal, time, note) VALUES (?, ?, ?, ?)",
                (key, ordinal, timestamp, note),
            )
        if fts5_enabled(conn):
            conn.execute(
                "INSERT INTO finding_search(finding_key, type, text) VALUES (?, ?, ?)",
                (key, finding_type, search_text(finding)),
            )


def migrate_legacy_json(root: Path, *, replace: bool = False) -> dict[str, int]:
    imported: dict[str, int] = {}
    with connect(root) as conn:
        ensure_schema(conn)
        for finding_type in TYPE_CHOICES:
            legacy = read_legacy_ledger(root, finding_type)
            if not legacy:
                continue
            existing = conn.execute("SELECT COUNT(*) AS count FROM findings WHERE type = ?", (finding_type,)).fetchone()
            if int(existing["count"]) and not replace:
                imported[finding_type] = 0
                continue
            findings = legacy.get("findings", [])
            replace_findings(conn, finding_type, findings)
            imported[finding_type] = len(findings)
        conn.commit()
    return imported


def initialize_workspace_db(root: Path, *, migrate_json: bool = True) -> InitResult:
    path = db_path(root)
    created = not path.exists()
    with connect(root) as conn:
        fts_enabled = ensure_schema(conn)
    imported = migrate_legacy_json(root, replace=False) if migrate_json else {}
    return InitResult(created=created, imported=imported, fts5_enabled=fts_enabled)


def load_ledger(root: Path, finding_type: str) -> dict[str, Any]:
    initialize_workspace_db(root)
    with connect(root) as conn:
        ensure_schema(conn)
        rows = conn.execute(
            "SELECT raw_json FROM findings WHERE type = ? ORDER BY created_at, id",
            (finding_type,),
        ).fetchall()
    return {
        "version": 2,
        "type": finding_type,
        "storage": DB_FILE,
        "findings": [json.loads(row["raw_json"]) for row in rows],
    }


def save_ledger(root: Path, finding_type: str, ledger: dict[str, Any]) -> None:
    initialize_workspace_db(root)
    findings = ledger.get("findings", [])
    if not isinstance(findings, list):
        raise SystemExit(f"{finding_type} ledger has invalid findings list")
    with connect(root) as conn:
        ensure_schema(conn)
        replace_findings(conn, finding_type, findings)
        conn.commit()


def all_ledgers(root: Path) -> dict[str, dict[str, Any]]:
    return {finding_type: load_ledger(root, finding_type) for finding_type in TYPE_CHOICES}


def fts_query(text: str) -> str:
    parts = sorted(token_set(text))
    return " OR ".join(f'"{part.replace(chr(34), chr(34) + chr(34))}"' for part in parts)


def semantic_search(root: Path, finding_types: list[str], query: str, limit: int) -> list[tuple[float, str, dict[str, Any]]]:
    initialize_workspace_db(root)
    query_text = fts_query(query)
    if not query_text:
        return []
    limit = max(1, limit)
    with connect(root) as conn:
        ensure_schema(conn)
        if fts5_enabled(conn):
            placeholders = ",".join("?" for _ in finding_types)
            sql = (
                "SELECT finding_search.type AS finding_type, findings.raw_json AS raw_json, "
                "bm25(finding_search) AS rank "
                "FROM finding_search JOIN findings USING(finding_key) "
                f"WHERE finding_search MATCH ? AND finding_search.type IN ({placeholders}) "
                "ORDER BY rank ASC LIMIT ?"
            )
            rows = conn.execute(sql, [query_text, *finding_types, limit]).fetchall()
            return [
                (round(-float(row["rank"]), 6), str(row["finding_type"]), json.loads(row["raw_json"]))
                for row in rows
            ]
        rows = conn.execute(
            f"SELECT type, raw_json FROM findings WHERE type IN ({','.join('?' for _ in finding_types)})",
            finding_types,
        ).fetchall()

    wanted = token_set(query)
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for row in rows:
        finding = json.loads(row["raw_json"])
        overlap = wanted & token_set(search_text(finding))
        if overlap:
            scored.append((-float(len(overlap)), str(row["type"]), finding))
    scored.sort(key=lambda item: (item[0], item[2].get("id", "")))
    return scored[:limit]
