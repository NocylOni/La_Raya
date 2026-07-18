"""Audit logging for the User & Security module."""
from __future__ import annotations

from app.db.database import Database


def log_action(
    db: Database,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
) -> int:
    return db.execute(
        "INSERT INTO audit_log(user_id, username, action, entity_type, entity_id, details) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, action, entity_type, entity_id, details),
    )


def list_audit_log(
    db: Database,
    limit: int = 200,
    entity_type: str | None = None,
    user_id: int | None = None,
) -> list:
    sql = "SELECT * FROM audit_log"
    clauses = []
    params: list = []
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if user_id:
        clauses.append("user_id = ?")
        params.append(user_id)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    return db.query(sql, tuple(params))
