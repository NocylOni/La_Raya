"""Module 9: Documents (referrals, discharge summaries, consent forms,
scanned records, PDFs, images) — stores files under the app data dir and
keeps a DB record pointing to them."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from app.db.database import Database, default_data_dir
from app.db.dao import search as search_dao

DOC_TYPES = ("referral", "discharge_summary", "consent", "scan", "image", "lab_report", "other")


def store_file(source_path: str | Path) -> str:
    """Copy an external file into the app's managed documents folder and
    return the stored path (relative-safe, unique filename)."""
    source_path = Path(source_path)
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    dest_dir = default_data_dir() / "documents"
    dest_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{source_path.name}"
    dest_path = dest_dir / unique_name
    shutil.copy2(source_path, dest_path)
    return str(dest_path)


def add_document(
    db: Database, patient_id: int, title: str, doc_type: str = "other",
    file_path: str | None = None, **fields
) -> int:
    if not title:
        raise ValueError("title is required")
    doc_id = db.execute(
        "INSERT INTO documents(patient_id, doc_type, title, file_path, uploaded_by, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (patient_id, doc_type, title, file_path, fields.get("uploaded_by"), fields.get("notes")),
    )
    search_dao.index_upsert(db, "document", doc_id, patient_id, title, fields.get("notes", ""))
    return doc_id


def list_documents(db: Database, patient_id: int, doc_type: str | None = None) -> list:
    if doc_type:
        return db.query(
            "SELECT * FROM documents WHERE patient_id = ? AND doc_type = ? "
            "ORDER BY uploaded_at DESC",
            (patient_id, doc_type),
        )
    return db.query(
        "SELECT * FROM documents WHERE patient_id = ? ORDER BY uploaded_at DESC", (patient_id,)
    )


def get_document(db: Database, doc_id: int):
    return db.query_one("SELECT * FROM documents WHERE id = ?", (doc_id,))


def delete_document(db: Database, doc_id: int, remove_file: bool = False) -> None:
    doc = get_document(db, doc_id)
    db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    search_dao.index_delete(db, "document", doc_id)
    if remove_file and doc and doc["file_path"]:
        path = Path(doc["file_path"])
        if path.exists():
            path.unlink()
