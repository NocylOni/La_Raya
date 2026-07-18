"""Module 7: Treatment Plan (therapies, referrals, follow-up, instructions, goals)."""
from __future__ import annotations

from app.db.database import Database


def create_plan(db: Database, patient_id: int, visit_id: int | None = None, **fields) -> int:
    return db.execute(
        "INSERT INTO treatment_plans(patient_id, visit_id, therapy, referral_to, "
        "follow_up_date, instructions, goals, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, visit_id, fields.get("therapy"), fields.get("referral_to"),
            fields.get("follow_up_date"), fields.get("instructions"), fields.get("goals"),
            fields.get("status", "open"),
        ),
    )


def update_plan(db: Database, plan_id: int, **fields) -> None:
    cols = [f for f in (
        "therapy", "referral_to", "follow_up_date", "instructions", "goals", "status",
    ) if f in fields]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    db.execute(
        f"UPDATE treatment_plans SET {set_clause} WHERE id = ?",
        tuple(fields[c] for c in cols) + (plan_id,),
    )


def list_plans(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM treatment_plans WHERE patient_id = ? ORDER BY created_at DESC",
        (patient_id,),
    )


def overdue_follow_ups(db: Database, as_of: str | None = None) -> list:
    """QoL clinical alert: open plans whose follow-up date has passed."""
    if as_of is None:
        return db.query(
            "SELECT tp.*, p.first_name, p.last_name, p.mrn FROM treatment_plans tp "
            "JOIN patients p ON p.id = tp.patient_id "
            "WHERE tp.status = 'open' AND tp.follow_up_date IS NOT NULL "
            "AND date(tp.follow_up_date) < date('now') ORDER BY tp.follow_up_date"
        )
    return db.query(
        "SELECT tp.*, p.first_name, p.last_name, p.mrn FROM treatment_plans tp "
        "JOIN patients p ON p.id = tp.patient_id "
        "WHERE tp.status = 'open' AND tp.follow_up_date IS NOT NULL "
        "AND date(tp.follow_up_date) < date(?) ORDER BY tp.follow_up_date",
        (as_of,),
    )


def delete_plan(db: Database, plan_id: int) -> None:
    db.execute("DELETE FROM treatment_plans WHERE id = ?", (plan_id,))
