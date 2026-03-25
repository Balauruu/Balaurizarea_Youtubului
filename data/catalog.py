"""CRUD module for the asset catalog SQLite database."""
import os, sys
os.environ.setdefault('PYTHONUTF8', '1')
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import sqlite3
from pathlib import Path

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS clips (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT NOT NULL,
    source_url  TEXT,
    source_type TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'analyzed',
    description TEXT,
    mood        TEXT,
    era         TEXT,
    duration_sec REAL,
    scope       TEXT NOT NULL,
    project     TEXT,
    category    TEXT,
    tags        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_clips_scope ON clips(scope);
CREATE INDEX IF NOT EXISTS idx_clips_project ON clips(project);
CREATE INDEX IF NOT EXISTS idx_clips_tags ON clips(tags);
"""

_DEFAULT_DB = Path(__file__).resolve().parent / "asset_catalog.db"


def init_db(db_path: Path | None = None) -> None:
    """Create schema if it doesn't exist."""
    path = db_path or _DEFAULT_DB
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a connection to the asset catalog. Creates schema if needed."""
    path = db_path or _DEFAULT_DB
    if not path.exists():
        init_db(path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def insert_clip(
    conn: sqlite3.Connection,
    path: str,
    source_type: str,
    scope: str,
    *,
    source_url: str | None = None,
    status: str = "analyzed",
    description: str | None = None,
    mood: str | None = None,
    era: str | None = None,
    duration_sec: float | None = None,
    project: str | None = None,
    category: str | None = None,
    tags: str | None = None,
) -> int:
    """Insert a new clip and return its id."""
    cur = conn.execute(
        """INSERT INTO clips
           (path, source_url, source_type, status, description,
            mood, era, duration_sec, scope, project, category, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (path, source_url, source_type, status, description,
         mood, era, duration_sec, scope, project, category, tags),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


_UPDATABLE = frozenset({
    "path", "source_url", "source_type", "status", "description",
    "mood", "era", "duration_sec", "scope", "project", "category", "tags",
})


def update_clip(conn: sqlite3.Connection, clip_id: int, **kwargs: object) -> None:
    """Update fields on a clip by id."""
    fields = {k: v for k, v in kwargs.items() if k in _UPDATABLE}
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(
        f"UPDATE clips SET {sets} WHERE id = ?",
        [*fields.values(), clip_id],
    )
    conn.commit()


def search_clips(
    conn: sqlite3.Connection,
    query: str,
    scope: str | None = None,
    project: str | None = None,
) -> list[dict]:
    """Text search across description and tags. Optional scope/project filter."""
    sql = "SELECT * FROM clips WHERE (description LIKE ? OR tags LIKE ?)"
    params: list[object] = [f"%{query}%", f"%{query}%"]
    if scope:
        sql += " AND scope = ?"
        params.append(scope)
    if project:
        sql += " AND project = ?"
        params.append(project)
    return [dict(row) for row in conn.execute(sql, params)]


def list_clips(
    conn: sqlite3.Connection,
    scope: str | None = None,
    project: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """List clips with optional filters."""
    sql = "SELECT * FROM clips WHERE 1=1"
    params: list[object] = []
    if scope:
        sql += " AND scope = ?"
        params.append(scope)
    if project:
        sql += " AND project = ?"
        params.append(project)
    if category:
        sql += " AND category = ?"
        params.append(category)
    return [dict(row) for row in conn.execute(sql, params)]


def delete_clip(conn: sqlite3.Connection, clip_id: int) -> None:
    """Remove a clip by id."""
    conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
    conn.commit()
