"""Module 12: Reporting & Analytics (patient summaries, outcome reports,
clinic statistics, disease registries)."""
from __future__ import annotations

from app.db.database import Database


def patient_summary(db: Database, patient_id: int) -> dict:
    patient = db.query_one("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        raise ValueError(f"No patient with id {patient_id}")
    counts = {}
    for label, table in (
        ("visits", "visits"), ("diagnoses", "diagnoses"),
        ("prescriptions", "prescriptions"), ("orders", "orders"),
        ("appointments", "appointments"), ("documents", "documents"),
    ):
        row = db.query_one(f"SELECT COUNT(*) AS n FROM {table} WHERE patient_id = ?", (patient_id,))
        counts[label] = row["n"]
    active_problems = db.query(
        "SELECT icd_code, description FROM diagnoses WHERE patient_id = ? AND status = 'active'",
        (patient_id,),
    )
    active_meds = db.query(
        "SELECT medication_name, dosage FROM prescriptions WHERE patient_id = ? AND status = 'active'",
        (patient_id,),
    )
    allergies = db.query(
        "SELECT substance, severity FROM allergies WHERE patient_id = ? AND status = 'active'",
        (patient_id,),
    )
    balance = db.query_one(
        "SELECT COALESCE(SUM(amount_due - amount_paid), 0) AS balance FROM invoices "
        "WHERE patient_id = ? AND status != 'void'",
        (patient_id,),
    )
    return {
        "patient": dict(patient),
        "counts": counts,
        "active_problems": [dict(r) for r in active_problems],
        "active_medications": [dict(r) for r in active_meds],
        "allergies": [dict(r) for r in allergies],
        "balance_due": balance["balance"],
    }


def clinic_statistics(db: Database, start_date: str | None = None, end_date: str | None = None) -> dict:
    date_filter = ""
    params: tuple = ()
    if start_date and end_date:
        date_filter = " WHERE date(visit_date) BETWEEN date(?) AND date(?)"
        params = (start_date, end_date)

    total_patients = db.query_one("SELECT COUNT(*) AS n FROM patients")["n"]
    total_visits = db.query_one(f"SELECT COUNT(*) AS n FROM visits{date_filter}", params)["n"]
    no_shows = db.query_one(
        "SELECT COUNT(*) AS n FROM appointments WHERE status = 'no-show'"
    )["n"]
    cancellations = db.query_one(
        "SELECT COUNT(*) AS n FROM appointments WHERE status = 'cancelled'"
    )["n"]
    revenue = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM payments"
    )["total"]
    outstanding = db.query_one(
        "SELECT COALESCE(SUM(amount_due - amount_paid), 0) AS total FROM invoices WHERE status != 'void'"
    )["total"]
    top_diagnoses = db.query(
        "SELECT icd_code, description, COUNT(*) AS n FROM diagnoses "
        "GROUP BY icd_code, description ORDER BY n DESC LIMIT 10"
    )
    return {
        "total_patients": total_patients,
        "total_visits": total_visits,
        "no_shows": no_shows,
        "cancellations": cancellations,
        "total_revenue": revenue,
        "outstanding_balance": outstanding,
        "top_diagnoses": [dict(r) for r in top_diagnoses],
    }


def disease_registry(db: Database, icd_code: str | None = None, description_like: str | None = None) -> list:
    """List all patients carrying a given diagnosis (chronic disease registry)."""
    sql = (
        "SELECT DISTINCT p.id, p.mrn, p.first_name, p.last_name, p.dob, d.icd_code, "
        "d.description, d.status FROM diagnoses d JOIN patients p ON p.id = d.patient_id"
    )
    clauses = []
    params: list = []
    if icd_code:
        clauses.append("d.icd_code = ?")
        params.append(icd_code)
    if description_like:
        clauses.append("d.description LIKE ?")
        params.append(f"%{description_like}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY p.last_name, p.first_name"
    return db.query(sql, tuple(params))
