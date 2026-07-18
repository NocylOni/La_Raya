"""Module 8: Appointments (scheduling, reminders, cancellations, no-shows)."""
from __future__ import annotations

from app.db.database import Database

STATUSES = ("scheduled", "completed", "cancelled", "no-show")


def schedule_appointment(
    db: Database, patient_id: int, appt_datetime: str, **fields
) -> int:
    if not appt_datetime:
        raise ValueError("appt_datetime is required")
    return db.execute(
        "INSERT INTO appointments(patient_id, provider, appt_datetime, duration_minutes, "
        "reason, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, fields.get("provider"), appt_datetime,
            fields.get("duration_minutes", 30), fields.get("reason"),
            fields.get("status", "scheduled"), fields.get("notes"),
        ),
    )


def reschedule_appointment(db: Database, appt_id: int, new_datetime: str) -> None:
    db.execute(
        "UPDATE appointments SET appt_datetime = ?, status = 'scheduled' WHERE id = ?",
        (new_datetime, appt_id),
    )


def update_status(db: Database, appt_id: int, status: str) -> None:
    if status not in STATUSES:
        raise ValueError(f"Unknown appointment status: {status}")
    db.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appt_id))


def mark_reminder_sent(db: Database, appt_id: int) -> None:
    db.execute("UPDATE appointments SET reminder_sent = 1 WHERE id = ?", (appt_id,))


def get_appointment(db: Database, appt_id: int):
    return db.query_one("SELECT * FROM appointments WHERE id = ?", (appt_id,))


def list_appointments(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM appointments WHERE patient_id = ? ORDER BY appt_datetime DESC",
        (patient_id,),
    )


def upcoming_appointments(db: Database, days_ahead: int = 7) -> list:
    return db.query(
        "SELECT a.*, p.first_name, p.last_name, p.mrn, p.phone FROM appointments a "
        "JOIN patients p ON p.id = a.patient_id "
        "WHERE a.status = 'scheduled' AND datetime(a.appt_datetime) BETWEEN datetime('now') "
        "AND datetime('now', ?) ORDER BY a.appt_datetime",
        (f"+{int(days_ahead)} days",),
    )


def todays_appointments(db: Database) -> list:
    return db.query(
        "SELECT a.*, p.first_name, p.last_name, p.mrn FROM appointments a "
        "JOIN patients p ON p.id = a.patient_id "
        "WHERE date(a.appt_datetime) = date('now') ORDER BY a.appt_datetime"
    )


def no_show_appointments(db: Database, patient_id: int | None = None) -> list:
    if patient_id:
        return db.query(
            "SELECT * FROM appointments WHERE status = 'no-show' AND patient_id = ? "
            "ORDER BY appt_datetime DESC",
            (patient_id,),
        )
    return db.query(
        "SELECT a.*, p.first_name, p.last_name FROM appointments a "
        "JOIN patients p ON p.id = a.patient_id "
        "WHERE a.status = 'no-show' ORDER BY a.appt_datetime DESC"
    )


def delete_appointment(db: Database, appt_id: int) -> None:
    db.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
