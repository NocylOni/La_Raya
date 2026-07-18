"""Templates for common conditions & customizable forms, plus autosave /
version history (QoL features)."""
from __future__ import annotations

import json

from app.db.database import Database


def create_template(db: Database, name: str, category: str, content: dict) -> int:
    if not name:
        raise ValueError("Template name is required")
    return db.execute(
        "INSERT INTO templates(name, category, content) VALUES (?, ?, ?)",
        (name, category, json.dumps(content)),
    )


def list_templates(db: Database, category: str | None = None) -> list:
    if category:
        rows = db.query("SELECT * FROM templates WHERE category = ? ORDER BY name", (category,))
    else:
        rows = db.query("SELECT * FROM templates ORDER BY category, name")
    return rows


def get_template(db: Database, template_id: int) -> dict | None:
    row = db.query_one("SELECT * FROM templates WHERE id = ?", (template_id,))
    if row is None:
        return None
    result = dict(row)
    result["content"] = json.loads(result["content"])
    return result


def delete_template(db: Database, template_id: int) -> None:
    db.execute("DELETE FROM templates WHERE id = ?", (template_id,))


# --------------------------------------------------------- autosave/versions
def save_draft(
    db: Database, entity_type: str, entity_id: int | None, patient_id: int | None,
    content: dict, user_id: int | None = None, is_autosave: bool = True
) -> int:
    return db.execute(
        "INSERT INTO draft_versions(entity_type, entity_id, patient_id, user_id, "
        "content_json, is_autosave) VALUES (?, ?, ?, ?, ?, ?)",
        (entity_type, entity_id, patient_id, user_id, json.dumps(content), int(is_autosave)),
    )


def list_versions(db: Database, entity_type: str, entity_id: int) -> list:
    rows = db.query(
        "SELECT * FROM draft_versions WHERE entity_type = ? AND entity_id IS ? "
        "ORDER BY saved_at DESC, id DESC",
        (entity_type, entity_id),
    )
    result = []
    for row in rows:
        d = dict(row)
        d["content"] = json.loads(d["content_json"])
        result.append(d)
    return result


def latest_draft(db: Database, entity_type: str, entity_id: int | None) -> dict | None:
    row = db.query_one(
        "SELECT * FROM draft_versions WHERE entity_type = ? AND entity_id IS ? "
        "ORDER BY saved_at DESC, id DESC LIMIT 1",
        (entity_type, entity_id),
    )
    if row is None:
        return None
    d = dict(row)
    d["content"] = json.loads(d["content_json"])
    return d
