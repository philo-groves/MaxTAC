"""Shared SQLite storage for MaxTAC workspace findings."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_FILE = "workspace.sqlite"
LEGACY_LEDGER_FILES = {
    "primitive": Path("primitives.json"),
    "chain": Path("chains.json"),
}
TYPE_CHOICES = tuple(LEGACY_LEDGER_FILES)
SCHEMA_VERSION = "2"


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

        CREATE TABLE IF NOT EXISTS debates (
          debate_id TEXT PRIMARY KEY,
          debate_dir TEXT NOT NULL,
          prompt_path TEXT NOT NULL,
          prompt_text TEXT NOT NULL,
          ballots INTEGER NOT NULL DEFAULT 0,
          yes_count INTEGER NOT NULL DEFAULT 0,
          no_count INTEGER NOT NULL DEFAULT 0,
          winner TEXT NOT NULL DEFAULT 'none',
          avg_yes_confidence REAL NOT NULL DEFAULT 0,
          avg_no_confidence REAL NOT NULL DEFAULT 0,
          tally_path TEXT NOT NULL DEFAULT '',
          summary_path TEXT NOT NULL DEFAULT '',
          updated_at TEXT NOT NULL,
          raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS debate_ballots (
          debate_id TEXT NOT NULL,
          file_path TEXT NOT NULL,
          subagent TEXT NOT NULL,
          goal_activation TEXT NOT NULL,
          choice TEXT NOT NULL,
          confidence INTEGER NOT NULL,
          reasoning TEXT NOT NULL,
          evidence TEXT NOT NULL,
          blockers TEXT,
          raw_json TEXT NOT NULL,
          PRIMARY KEY (debate_id, file_path),
          FOREIGN KEY (debate_id) REFERENCES debates(debate_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audits (
          audit_id TEXT PRIMARY KEY,
          audit_dir TEXT NOT NULL,
          prompt_path TEXT NOT NULL,
          assessment_path TEXT NOT NULL,
          prompt_text TEXT NOT NULL,
          assessment_text TEXT NOT NULL,
          goal_activation TEXT NOT NULL DEFAULT '',
          conclusion TEXT NOT NULL DEFAULT '',
          updated_at TEXT NOT NULL,
          raw_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_artifacts (
          audit_id TEXT NOT NULL,
          path TEXT NOT NULL,
          kind TEXT NOT NULL,
          size INTEGER NOT NULL,
          mtime_utc TEXT NOT NULL,
          PRIMARY KEY (audit_id, path),
          FOREIGN KEY (audit_id) REFERENCES audits(audit_id) ON DELETE CASCADE
        );
        """
    )
    set_meta(conn, "schema_version", SCHEMA_VERSION)
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS finding_search USING fts5("
            "finding_key UNINDEXED, type UNINDEXED, text, tokenize='porter unicode61')"
        )
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS debate_search USING fts5("
            "debate_id UNINDEXED, text, tokenize='porter unicode61')"
        )
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS audit_search USING fts5("
            "audit_id UNINDEXED, text, tokenize='porter unicode61')"
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


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_optional_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def path_mtime(path: Path) -> str:
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat()


def newest_mtime(paths: list[Path]) -> str:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return max(path_mtime(path) for path in existing)


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


def ballot_value(ballot: dict[str, Any], key: str, default: str = "") -> str:
    value = ballot.get(key, default)
    if value is None:
        return ""
    return str(value)


def debate_payload_from_dir(root: Path, debate_dir: Path) -> dict[str, Any]:
    debate_id = debate_dir.name
    prompt_path = debate_dir / "prompt.md"
    tally_path = debate_dir / "tally.json"
    summary_path = debate_dir / "summary.md"
    prompt_text = read_optional_text(prompt_path)
    ballot_details: list[dict[str, Any]] = []
    counts = {"yes": 0, "no": 0}
    confidence_totals = {"yes": 0, "no": 0}

    for ballot_path in sorted(debate_dir.glob("ballot-*.json")):
        try:
            ballot = json.loads(ballot_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{ballot_path} is not valid JSON: {exc}") from exc
        if not isinstance(ballot, dict):
            raise SystemExit(f"{ballot_path} must contain a JSON object")
        choice = ballot_value(ballot, "choice").lower()
        if choice not in {"yes", "no"}:
            raise SystemExit(f"{ballot_path} ballot choice must be yes or no")
        confidence = ballot.get("confidence")
        if not isinstance(confidence, int):
            raise SystemExit(f"{ballot_path} ballot confidence must be an integer")
        counts[choice] += 1
        confidence_totals[choice] += confidence
        ballot_details.append(
            {
                "file": relative_to_root(root, ballot_path),
                "subagent": ballot_value(ballot, "subagent", ballot_path.stem.removeprefix("ballot-")),
                "goal_activation": ballot_value(ballot, "goal_activation", "unknown"),
                "choice": choice,
                "confidence": confidence,
                "reasoning": ballot_value(ballot, "reasoning"),
                "evidence": ballot_value(ballot, "evidence"),
                "blockers": ballot.get("blockers"),
                "raw": ballot,
            }
        )

    if counts["yes"] > counts["no"]:
        winner = "yes"
    elif counts["no"] > counts["yes"]:
        winner = "no"
    elif ballot_details:
        winner = "tie"
    else:
        winner = "none"

    return {
        "debate_id": debate_id,
        "debate_dir": relative_to_root(root, debate_dir),
        "prompt_path": relative_to_root(root, prompt_path) if prompt_path.exists() else "",
        "prompt_text": prompt_text,
        "ballots": len(ballot_details),
        "counts": counts,
        "average_confidence": {
            choice: (confidence_totals[choice] / counts[choice] if counts[choice] else 0)
            for choice in ("yes", "no")
        },
        "winner": winner,
        "tally_path": relative_to_root(root, tally_path) if tally_path.exists() else "",
        "summary_path": relative_to_root(root, summary_path) if summary_path.exists() else "",
        "ballot_details": ballot_details,
        "updated_at": newest_mtime([prompt_path, tally_path, summary_path, *sorted(debate_dir.glob("ballot-*.json"))]),
    }


def debate_search_text(payload: dict[str, Any]) -> str:
    return " ".join(
        [
            str(payload.get("debate_id", "")),
            str(payload.get("prompt_text", "")),
            json.dumps(payload.get("counts", {}), sort_keys=True),
            str(payload.get("winner", "")),
            " ".join(text_values(payload.get("ballot_details", []))),
        ]
    )


def upsert_debate(conn: sqlite3.Connection, payload: dict[str, Any]) -> None:
    debate_id = str(payload["debate_id"])
    conn.execute("DELETE FROM debate_ballots WHERE debate_id = ?", (debate_id,))
    if fts5_enabled(conn):
        conn.execute("DELETE FROM debate_search WHERE debate_id = ?", (debate_id,))
    raw_json = json.dumps(payload, sort_keys=True)
    conn.execute(
        """
        INSERT INTO debates(
          debate_id, debate_dir, prompt_path, prompt_text, ballots, yes_count, no_count,
          winner, avg_yes_confidence, avg_no_confidence, tally_path, summary_path,
          updated_at, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(debate_id) DO UPDATE SET
          debate_dir=excluded.debate_dir,
          prompt_path=excluded.prompt_path,
          prompt_text=excluded.prompt_text,
          ballots=excluded.ballots,
          yes_count=excluded.yes_count,
          no_count=excluded.no_count,
          winner=excluded.winner,
          avg_yes_confidence=excluded.avg_yes_confidence,
          avg_no_confidence=excluded.avg_no_confidence,
          tally_path=excluded.tally_path,
          summary_path=excluded.summary_path,
          updated_at=excluded.updated_at,
          raw_json=excluded.raw_json
        """,
        (
            debate_id,
            str(payload.get("debate_dir", "")),
            str(payload.get("prompt_path", "")),
            str(payload.get("prompt_text", "")),
            int(payload.get("ballots", 0)),
            int(payload.get("counts", {}).get("yes", 0)),
            int(payload.get("counts", {}).get("no", 0)),
            str(payload.get("winner", "none")),
            float(payload.get("average_confidence", {}).get("yes", 0)),
            float(payload.get("average_confidence", {}).get("no", 0)),
            str(payload.get("tally_path", "")),
            str(payload.get("summary_path", "")),
            str(payload.get("updated_at", "")),
            raw_json,
        ),
    )
    for ballot in payload.get("ballot_details", []):
        conn.execute(
            """
            INSERT INTO debate_ballots(
              debate_id, file_path, subagent, goal_activation, choice, confidence,
              reasoning, evidence, blockers, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                debate_id,
                str(ballot.get("file", "")),
                str(ballot.get("subagent", "")),
                str(ballot.get("goal_activation", "")),
                str(ballot.get("choice", "")),
                int(ballot.get("confidence", 0)),
                str(ballot.get("reasoning", "")),
                str(ballot.get("evidence", "")),
                None if ballot.get("blockers") is None else str(ballot.get("blockers")),
                json.dumps(ballot.get("raw", {}), sort_keys=True),
            ),
        )
    if fts5_enabled(conn):
        conn.execute(
            "INSERT INTO debate_search(debate_id, text) VALUES (?, ?)",
            (debate_id, debate_search_text(payload)),
        )


def sync_debates(root: Path, debate_id: str | None = None) -> list[dict[str, Any]]:
    initialize_workspace_db(root)
    debates_dir = root / "debates"
    if debate_id:
        candidates = [debates_dir / debate_id]
    else:
        candidates = sorted(path for path in debates_dir.glob("*") if path.is_dir()) if debates_dir.exists() else []
    payloads = [debate_payload_from_dir(root, path) for path in candidates if path.exists() and path.is_dir()]
    with connect(root) as conn:
        ensure_schema(conn)
        for payload in payloads:
            upsert_debate(conn, payload)
        conn.commit()
    return payloads


def list_debates(root: Path, *, sync: bool = True) -> list[dict[str, Any]]:
    if sync:
        sync_debates(root)
    with connect(root) as conn:
        ensure_schema(conn)
        rows = conn.execute("SELECT raw_json FROM debates ORDER BY updated_at DESC, debate_id DESC").fetchall()
    return [json.loads(row["raw_json"]) for row in rows]


def get_debate(root: Path, debate_id: str, *, sync: bool = True) -> dict[str, Any] | None:
    if sync:
        sync_debates(root, debate_id)
    with connect(root) as conn:
        ensure_schema(conn)
        row = conn.execute("SELECT raw_json FROM debates WHERE debate_id = ?", (debate_id,)).fetchone()
    return json.loads(row["raw_json"]) if row else None


def semantic_search_debates(root: Path, query: str, limit: int, *, sync: bool = True) -> list[tuple[float, dict[str, Any]]]:
    if sync:
        sync_debates(root)
    query_text = fts_query(query)
    if not query_text:
        return []
    limit = max(1, limit)
    with connect(root) as conn:
        ensure_schema(conn)
        if fts5_enabled(conn):
            rows = conn.execute(
                """
                SELECT debates.raw_json AS raw_json, bm25(debate_search) AS rank
                FROM debate_search JOIN debates USING(debate_id)
                WHERE debate_search MATCH ?
                ORDER BY rank ASC LIMIT ?
                """,
                (query_text, limit),
            ).fetchall()
            return [(round(-float(row["rank"]), 6), json.loads(row["raw_json"])) for row in rows]
        rows = conn.execute("SELECT raw_json FROM debates").fetchall()
    wanted = token_set(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        payload = json.loads(row["raw_json"])
        overlap = wanted & token_set(debate_search_text(payload))
        if overlap:
            scored.append((float(len(overlap)), payload))
    scored.sort(key=lambda item: (item[0], item[1].get("updated_at", "")), reverse=True)
    return scored[:limit]


def extract_heading_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^#+\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"^#+\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def extract_goal_activation(assessment: str) -> str:
    section = extract_heading_section(assessment, "Goal Activation")
    if not section:
        match = re.search(r"Goal activation:\s*([^\n]+)", assessment, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    first = section.splitlines()[0].strip() if section.splitlines() else ""
    return first.strip("- `")


def extract_conclusion(assessment: str) -> str:
    for heading in ("Conclusion", "Verdict", "Assessment", "Findings"):
        section = extract_heading_section(assessment, heading)
        if section:
            return section[:1200]
    return assessment[:1200]


def audit_payload_from_dir(root: Path, audit_dir: Path) -> dict[str, Any]:
    audit_id = audit_dir.name
    prompt_path = audit_dir / "prompt.md"
    assessment_path = audit_dir / "assessment.md"
    prompt_text = read_optional_text(prompt_path)
    assessment_text = read_optional_text(assessment_path)
    artifacts: list[dict[str, Any]] = []
    for path in sorted(item for item in audit_dir.rglob("*") if item.is_file()):
        if path.name in {"prompt.md", "assessment.md"}:
            continue
        artifacts.append(
            {
                "path": relative_to_root(root, path),
                "kind": path.suffix.lower().lstrip(".") or "file",
                "size": path.stat().st_size,
                "mtime_utc": path_mtime(path),
            }
        )
    return {
        "audit_id": audit_id,
        "audit_dir": relative_to_root(root, audit_dir),
        "prompt_path": relative_to_root(root, prompt_path) if prompt_path.exists() else "",
        "assessment_path": relative_to_root(root, assessment_path) if assessment_path.exists() else "",
        "prompt_text": prompt_text,
        "assessment_text": assessment_text,
        "goal_activation": extract_goal_activation(assessment_text),
        "conclusion": extract_conclusion(assessment_text),
        "artifacts": artifacts,
        "updated_at": newest_mtime([prompt_path, assessment_path, *[root / item["path"] for item in artifacts]]),
    }


def audit_search_text(payload: dict[str, Any]) -> str:
    return " ".join(
        [
            str(payload.get("audit_id", "")),
            str(payload.get("prompt_text", "")),
            str(payload.get("assessment_text", "")),
            str(payload.get("goal_activation", "")),
            str(payload.get("conclusion", "")),
            " ".join(text_values(payload.get("artifacts", []))),
        ]
    )


def upsert_audit(conn: sqlite3.Connection, payload: dict[str, Any]) -> None:
    audit_id = str(payload["audit_id"])
    conn.execute("DELETE FROM audit_artifacts WHERE audit_id = ?", (audit_id,))
    if fts5_enabled(conn):
        conn.execute("DELETE FROM audit_search WHERE audit_id = ?", (audit_id,))
    raw_json = json.dumps(payload, sort_keys=True)
    conn.execute(
        """
        INSERT INTO audits(
          audit_id, audit_dir, prompt_path, assessment_path, prompt_text,
          assessment_text, goal_activation, conclusion, updated_at, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(audit_id) DO UPDATE SET
          audit_dir=excluded.audit_dir,
          prompt_path=excluded.prompt_path,
          assessment_path=excluded.assessment_path,
          prompt_text=excluded.prompt_text,
          assessment_text=excluded.assessment_text,
          goal_activation=excluded.goal_activation,
          conclusion=excluded.conclusion,
          updated_at=excluded.updated_at,
          raw_json=excluded.raw_json
        """,
        (
            audit_id,
            str(payload.get("audit_dir", "")),
            str(payload.get("prompt_path", "")),
            str(payload.get("assessment_path", "")),
            str(payload.get("prompt_text", "")),
            str(payload.get("assessment_text", "")),
            str(payload.get("goal_activation", "")),
            str(payload.get("conclusion", "")),
            str(payload.get("updated_at", "")),
            raw_json,
        ),
    )
    for artifact in payload.get("artifacts", []):
        conn.execute(
            """
            INSERT INTO audit_artifacts(audit_id, path, kind, size, mtime_utc)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                str(artifact.get("path", "")),
                str(artifact.get("kind", "")),
                int(artifact.get("size", 0)),
                str(artifact.get("mtime_utc", "")),
            ),
        )
    if fts5_enabled(conn):
        conn.execute(
            "INSERT INTO audit_search(audit_id, text) VALUES (?, ?)",
            (audit_id, audit_search_text(payload)),
        )


def sync_audits(root: Path, audit_id: str | None = None) -> list[dict[str, Any]]:
    initialize_workspace_db(root)
    audits_dir = root / "audits"
    if audit_id:
        candidates = [audits_dir / audit_id]
    else:
        candidates = sorted(path for path in audits_dir.glob("*") if path.is_dir()) if audits_dir.exists() else []
    payloads = [audit_payload_from_dir(root, path) for path in candidates if path.exists() and path.is_dir()]
    with connect(root) as conn:
        ensure_schema(conn)
        for payload in payloads:
            upsert_audit(conn, payload)
        conn.commit()
    return payloads


def list_audits(root: Path, *, sync: bool = True) -> list[dict[str, Any]]:
    if sync:
        sync_audits(root)
    with connect(root) as conn:
        ensure_schema(conn)
        rows = conn.execute("SELECT raw_json FROM audits ORDER BY updated_at DESC, audit_id DESC").fetchall()
    return [json.loads(row["raw_json"]) for row in rows]


def get_audit(root: Path, audit_id: str, *, sync: bool = True) -> dict[str, Any] | None:
    if sync:
        sync_audits(root, audit_id)
    with connect(root) as conn:
        ensure_schema(conn)
        row = conn.execute("SELECT raw_json FROM audits WHERE audit_id = ?", (audit_id,)).fetchone()
    return json.loads(row["raw_json"]) if row else None


def semantic_search_audits(root: Path, query: str, limit: int, *, sync: bool = True) -> list[tuple[float, dict[str, Any]]]:
    if sync:
        sync_audits(root)
    query_text = fts_query(query)
    if not query_text:
        return []
    limit = max(1, limit)
    with connect(root) as conn:
        ensure_schema(conn)
        if fts5_enabled(conn):
            rows = conn.execute(
                """
                SELECT audits.raw_json AS raw_json, bm25(audit_search) AS rank
                FROM audit_search JOIN audits USING(audit_id)
                WHERE audit_search MATCH ?
                ORDER BY rank ASC LIMIT ?
                """,
                (query_text, limit),
            ).fetchall()
            return [(round(-float(row["rank"]), 6), json.loads(row["raw_json"])) for row in rows]
        rows = conn.execute("SELECT raw_json FROM audits").fetchall()
    wanted = token_set(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        payload = json.loads(row["raw_json"])
        overlap = wanted & token_set(audit_search_text(payload))
        if overlap:
            scored.append((float(len(overlap)), payload))
    scored.sort(key=lambda item: (item[0], item[1].get("updated_at", "")), reverse=True)
    return scored[:limit]


def count_debates(root: Path) -> int:
    with connect(root) as conn:
        ensure_schema(conn)
        row = conn.execute("SELECT COUNT(*) AS count FROM debates").fetchone()
    return int(row["count"])


def count_audits(root: Path) -> int:
    with connect(root) as conn:
        ensure_schema(conn)
        row = conn.execute("SELECT COUNT(*) AS count FROM audits").fetchone()
    return int(row["count"])
