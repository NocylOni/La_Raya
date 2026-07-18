"""Module 4: Diagnoses (ICD-10/ICD-11 codes, problem list, chronic conditions)."""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import search as search_dao


def add_diagnosis(
    db: Database, patient_id: int, icd_code: str, description: str,
    visit_id: int | None = None, icd_system: str = "ICD-10", **fields
) -> int:
    if not icd_code or not description:
        raise ValueError("icd_code and description are required")
    diag_id = db.execute(
        "INSERT INTO diagnoses(patient_id, visit_id, icd_code, icd_system, description, "
        "status, chronic, onset_date, resolved_date, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, visit_id, icd_code, icd_system, description,
            fields.get("status", "active"), int(bool(fields.get("chronic", False))),
            fields.get("onset_date"), fields.get("resolved_date"), fields.get("notes"),
        ),
    )
    search_dao.index_upsert(
        db, "diagnosis", diag_id, patient_id, f"{icd_code} {description}",
        fields.get("notes", ""),
    )
    return diag_id


def update_diagnosis(db: Database, diagnosis_id: int, **fields) -> None:
    cols = [f for f in ("status", "chronic", "resolved_date", "notes", "description")
            if f in fields]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    values = [int(bool(fields[c])) if c == "chronic" else fields[c] for c in cols]
    db.execute(
        f"UPDATE diagnoses SET {set_clause} WHERE id = ?", tuple(values) + (diagnosis_id,)
    )


def get_diagnosis(db: Database, diagnosis_id: int):
    return db.query_one("SELECT * FROM diagnoses WHERE id = ?", (diagnosis_id,))


def list_diagnoses(db: Database, patient_id: int, status: str | None = None) -> list:
    if status:
        return db.query(
            "SELECT * FROM diagnoses WHERE patient_id = ? AND status = ? "
            "ORDER BY onset_date DESC, id DESC",
            (patient_id, status),
        )
    return db.query(
        "SELECT * FROM diagnoses WHERE patient_id = ? ORDER BY status, onset_date DESC",
        (patient_id,),
    )


def problem_list(db: Database, patient_id: int) -> list:
    """Active problem list (module requirement)."""
    return db.query(
        "SELECT * FROM diagnoses WHERE patient_id = ? AND status = 'active' "
        "ORDER BY chronic DESC, onset_date DESC",
        (patient_id,),
    )


def chronic_conditions(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM diagnoses WHERE patient_id = ? AND chronic = 1 ORDER BY onset_date",
        (patient_id,),
    )


def delete_diagnosis(db: Database, diagnosis_id: int) -> None:
    db.execute("DELETE FROM diagnoses WHERE id = ?", (diagnosis_id,))
    search_dao.index_delete(db, "diagnosis", diagnosis_id)
