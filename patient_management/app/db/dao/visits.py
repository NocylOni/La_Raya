"""Module 3: Visits / Encounters (SOAP notes and vital signs)."""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import search as search_dao

VISIT_FIELDS = (
    "visit_date", "provider", "visit_type", "chief_complaint", "hpi", "ros",
    "physical_exam", "assessment", "plan", "notes",
)


def _index_visit(db: Database, visit_id: int) -> None:
    row = db.query_one("SELECT * FROM visits WHERE id = ?", (visit_id,))
    if row is None:
        return
    title = f"Visit {row['visit_date']} - {row['chief_complaint'] or row['visit_type']}"
    content = " ".join(
        str(row[f]) for f in ("chief_complaint", "hpi", "ros", "physical_exam",
                               "assessment", "plan", "notes")
        if row[f]
    )
    search_dao.index_upsert(db, "visit", visit_id, row["patient_id"], title, content)


def create_visit(db: Database, patient_id: int, **fields) -> int:
    # Omit blank fields so NOT NULL DEFAULT columns like `visit_date` fall
    # back to their DB default instead of erroring out.
    cols = [f for f in VISIT_FIELDS if f in fields and fields[f] is not None]
    col_sql = ", ".join(["patient_id"] + cols)
    placeholders = ", ".join(["?"] * (len(cols) + 1))
    sql = f"INSERT INTO visits({col_sql}) VALUES ({placeholders})"
    values = [patient_id] + [fields[c] for c in cols]
    visit_id = db.execute(sql, tuple(values))
    _index_visit(db, visit_id)
    return visit_id


def update_visit(db: Database, visit_id: int, **fields) -> None:
    cols = [f for f in VISIT_FIELDS if f in fields and fields[f] is not None]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    sql = f"UPDATE visits SET {set_clause}, updated_at = datetime('now') WHERE id = ?"
    db.execute(sql, tuple(fields[c] for c in cols) + (visit_id,))
    _index_visit(db, visit_id)


def get_visit(db: Database, visit_id: int):
    return db.query_one("SELECT * FROM visits WHERE id = ?", (visit_id,))


def list_visits(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM visits WHERE patient_id = ? ORDER BY visit_date DESC", (patient_id,)
    )


def delete_visit(db: Database, visit_id: int) -> None:
    db.execute("DELETE FROM visits WHERE id = ?", (visit_id,))
    search_dao.index_delete(db, "visit", visit_id)


# --------------------------------------------------------------- vitals
def _compute_bmi(height_cm: float | None, weight_kg: float | None) -> float | None:
    if not height_cm or not weight_kg:
        return None
    height_m = height_cm / 100.0
    if height_m <= 0:
        return None
    return round(weight_kg / (height_m ** 2), 1)


def record_vitals(db: Database, patient_id: int, visit_id: int | None = None, **fields) -> int:
    bmi = fields.get("bmi") or _compute_bmi(fields.get("height_cm"), fields.get("weight_kg"))
    return db.execute(
        "INSERT INTO vitals(patient_id, visit_id, recorded_at, height_cm, weight_kg, bmi, "
        "temp_c, heart_rate, resp_rate, bp_systolic, bp_diastolic, spo2, pain_score) "
        "VALUES (?, ?, COALESCE(?, datetime('now')), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, visit_id, fields.get("recorded_at"), fields.get("height_cm"),
            fields.get("weight_kg"), bmi, fields.get("temp_c"), fields.get("heart_rate"),
            fields.get("resp_rate"), fields.get("bp_systolic"), fields.get("bp_diastolic"),
            fields.get("spo2"), fields.get("pain_score"),
        ),
    )


def list_vitals(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at", (patient_id,)
    )


def delete_vitals(db: Database, vitals_id: int) -> None:
    db.execute("DELETE FROM vitals WHERE id = ?", (vitals_id,))
