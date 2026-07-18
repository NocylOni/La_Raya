"""Full-text search index maintenance and querying (QoL: full-text search)."""
from __future__ import annotations

from app.db.database import Database


def index_upsert(
    db: Database,
    entity_type: str,
    entity_id: int,
    patient_id: int | None,
    title: str,
    content: str,
) -> None:
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        cur.execute(
            "INSERT INTO search_index(entity_type, entity_id, patient_id, title, content) "
            "VALUES (?, ?, ?, ?, ?)",
            (entity_type, entity_id, patient_id, title or "", content or ""),
        )


def index_delete(db: Database, entity_type: str, entity_id: int) -> None:
    db.execute(
        "DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id),
    )


def _escape_fts_query(text: str) -> str:
    # Wrap each token in double quotes so punctuation / FTS operators in
    # free-text user input can't break the MATCH query syntax, and add a
    # trailing wildcard for prefix search.
    tokens = [t for t in text.replace('"', " ").split() if t]
    if not tokens:
        return ""
    return " ".join(f'"{t}"*' for t in tokens)


def full_text_search(
    db: Database, query: str, patient_id: int | None = None, limit: int = 50
) -> list:
    fts_query = _escape_fts_query(query)
    if not fts_query:
        return []
    sql = (
        "SELECT entity_type, entity_id, patient_id, title, "
        "snippet(search_index, 4, '[', ']', '...', 10) AS snippet "
        "FROM search_index WHERE search_index MATCH ?"
    )
    params: list = [fts_query]
    if patient_id is not None:
        sql += " AND patient_id = ?"
        params.append(patient_id)
    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)
    return db.query(sql, tuple(params))
