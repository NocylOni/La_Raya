"""Module 2: Medical History (past medical/surgical, family, social history,
medications, immunizations)."""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import search as search_dao

HISTORY_CATEGORIES = ("past_medical", "past_surgical", "family", "social")


def add_history_item(
    db: Database, patient_id: int, category: str, description: str, **fields
) -> int:
    if category not in HISTORY_CATEGORIES:
        raise ValueError(f"Unknown history category: {category}")
    if not description:
        raise ValueError("Description is required")
    item_id = db.execute(
        "INSERT INTO medical_history(patient_id, category, description, onset_date, "
        "resolved_date, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, category, description, fields.get("onset_date"),
            fields.get("resolved_date"), fields.get("status", "active"),
            fields.get("notes"),
        ),
    )
    search_dao.index_upsert(db, "medical_history", item_id, patient_id, description,
                             fields.get("notes", ""))
    return item_id


def list_history(db: Database, patient_id: int, category: str | None = None) -> list:
    if category:
        return db.query(
            "SELECT * FROM medical_history WHERE patient_id = ? AND category = ? ORDER BY id",
            (patient_id, category),
        )
    return db.query(
        "SELECT * FROM medical_history WHERE patient_id = ? ORDER BY category, id",
        (patient_id,),
    )


def delete_history_item(db: Database, item_id: int) -> None:
    db.execute("DELETE FROM medical_history WHERE id = ?", (item_id,))
    search_dao.index_delete(db, "medical_history", item_id)


def update_history_item(db: Database, item_id: int, **fields) -> None:
    cols = [f for f in ("description", "onset_date", "resolved_date", "status", "notes")
            if f in fields]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    db.execute(
        f"UPDATE medical_history SET {set_clause} WHERE id = ?",
        tuple(fields[c] for c in cols) + (item_id,),
    )


# ------------------------------------------------------------ immunizations
def add_immunization(db: Database, patient_id: int, vaccine: str, **fields) -> int:
    if not vaccine:
        raise ValueError("Vaccine name is required")
    return db.execute(
        "INSERT INTO immunizations(patient_id, vaccine, date_given, dose, lot_number, "
        "site, provider, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, vaccine, fields.get("date_given"), fields.get("dose"),
            fields.get("lot_number"), fields.get("site"), fields.get("provider"),
            fields.get("notes"),
        ),
    )


def list_immunizations(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM immunizations WHERE patient_id = ? ORDER BY date_given DESC",
        (patient_id,),
    )


def delete_immunization(db: Database, immunization_id: int) -> None:
    db.execute("DELETE FROM immunizations WHERE id = ?", (immunization_id,))


# --------------------------------------------------------- medication hist.
def add_medication_history(db: Database, patient_id: int, name: str, **fields) -> int:
    if not name:
        raise ValueError("Medication name is required")
    return db.execute(
        "INSERT INTO medication_history(patient_id, name, dosage, route, frequency, "
        "start_date, end_date, status, prescribing_provider, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, name, fields.get("dosage"), fields.get("route"),
            fields.get("frequency"), fields.get("start_date"), fields.get("end_date"),
            fields.get("status", "active"), fields.get("prescribing_provider"),
            fields.get("notes"),
        ),
    )


def list_medication_history(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM medication_history WHERE patient_id = ? ORDER BY start_date DESC",
        (patient_id,),
    )


def delete_medication_history(db: Database, item_id: int) -> None:
    db.execute("DELETE FROM medication_history WHERE id = ?", (item_id,))
