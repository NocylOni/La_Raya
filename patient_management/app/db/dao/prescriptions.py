"""Module 6: Prescriptions (medications, dosage, refills, history).

Interaction / allergy alerting lives in app.logic.alerts and is invoked by
the GUI layer before/after calling create_prescription so the DAO stays a
pure data-access layer.
"""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import search as search_dao


def create_prescription(
    db: Database, patient_id: int, medication_name: str, visit_id: int | None = None,
    **fields
) -> int:
    if not medication_name:
        raise ValueError("medication_name is required")
    refills = fields.get("refills", 0)
    rx_id = db.execute(
        "INSERT INTO prescriptions(patient_id, visit_id, medication_name, dosage, route, "
        "frequency, duration, quantity, refills, refills_remaining, prescriber, status, "
        "start_date, end_date, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, date('now')), ?, ?)",
        (
            patient_id, visit_id, medication_name, fields.get("dosage"), fields.get("route"),
            fields.get("frequency"), fields.get("duration"), fields.get("quantity"),
            refills, fields.get("refills_remaining", refills), fields.get("prescriber"),
            fields.get("status", "active"), fields.get("start_date"), fields.get("end_date"),
            fields.get("notes"),
        ),
    )
    search_dao.index_upsert(
        db, "prescription", rx_id, patient_id, medication_name,
        f"{fields.get('dosage', '')} {fields.get('frequency', '')} {fields.get('notes', '')}",
    )
    return rx_id


def update_prescription(db: Database, rx_id: int, **fields) -> None:
    cols = [f for f in (
        "dosage", "route", "frequency", "duration", "quantity", "refills",
        "refills_remaining", "status", "end_date", "notes",
    ) if f in fields]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    db.execute(
        f"UPDATE prescriptions SET {set_clause} WHERE id = ?",
        tuple(fields[c] for c in cols) + (rx_id,),
    )


def refill_prescription(db: Database, rx_id: int) -> bool:
    row = db.query_one("SELECT refills_remaining FROM prescriptions WHERE id = ?", (rx_id,))
    if row is None or row["refills_remaining"] <= 0:
        return False
    db.execute(
        "UPDATE prescriptions SET refills_remaining = refills_remaining - 1 WHERE id = ?",
        (rx_id,),
    )
    return True


def get_prescription(db: Database, rx_id: int):
    return db.query_one("SELECT * FROM prescriptions WHERE id = ?", (rx_id,))


def list_prescriptions(db: Database, patient_id: int, active_only: bool = False) -> list:
    if active_only:
        return db.query(
            "SELECT * FROM prescriptions WHERE patient_id = ? AND status = 'active' "
            "ORDER BY start_date DESC",
            (patient_id,),
        )
    return db.query(
        "SELECT * FROM prescriptions WHERE patient_id = ? ORDER BY start_date DESC",
        (patient_id,),
    )


def delete_prescription(db: Database, rx_id: int) -> None:
    db.execute("DELETE FROM prescriptions WHERE id = ?", (rx_id,))
    search_dao.index_delete(db, "prescription", rx_id)
