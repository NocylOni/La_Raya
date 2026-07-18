"""Connection management, initialization and backup utilities."""
from __future__ import annotations

import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from app.db.schema import SCHEMA_SQL, SCHEMA_VERSION

DEFAULT_DB_NAME = "patient_management.db"


def default_data_dir() -> Path:
    """Directory where the database and backups/documents live.

    Uses a user-writable location so the packaged executable can run
    without admin rights: %APPDATA%/PatientManagement on Windows,
    ~/.patient_management elsewhere.
    """
    import os
    import sys

    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home())
        path = Path(base) / "PatientManagement"
    else:
        path = Path.home() / ".patient_management"
    path.mkdir(parents=True, exist_ok=True)
    (path / "documents").mkdir(exist_ok=True)
    (path / "backups").mkdir(exist_ok=True)
    return path


class Database:
    """Thin wrapper around a single sqlite3 connection with helpers."""

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            db_path = default_data_dir() / DEFAULT_DB_NAME
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self.init_schema()

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def init_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        cur = self._conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'version'"
        )
        row = cur.fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO schema_meta(key, value) VALUES ('version', ?)",
                (str(SCHEMA_VERSION),),
            )
        self._conn.commit()

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self.cursor() as cur:
            cur.execute(sql, params)
            last_id = cur.lastrowid
        return last_id

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        cur = self._conn.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        cur = self._conn.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    def backup(self, backup_dir: str | Path | None = None) -> Path:
        """Create a timestamped copy of the database file (automatic backups)."""
        if backup_dir is None:
            backup_dir = default_data_dir() / "backups"
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = backup_dir / f"backup_{stamp}.db"
        self._conn.commit()
        dest_conn = sqlite3.connect(str(dest))
        with dest_conn:
            self._conn.backup(dest_conn)
        dest_conn.close()
        return dest

    def close(self) -> None:
        self._conn.close()


_singleton: Database | None = None


def get_db(db_path: str | Path | None = None, force_new: bool = False) -> Database:
    """Return a process-wide Database instance (created on first call)."""
    global _singleton
    if force_new or _singleton is None:
        _singleton = Database(db_path)
    return _singleton


def reset_singleton() -> None:
    """Used by tests to force a fresh Database on next get_db() call."""
    global _singleton
    if _singleton is not None:
        _singleton.close()
    _singleton = None
