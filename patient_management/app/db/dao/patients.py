"""Module 1: Patient Registry (demographics, contact, insurance,
emergency contacts, allergies, primary care physician)."""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import search as search_dao

PATIENT_FIELDS = (
    "mrn", "first_name", "last_name", "dob", "sex", "gender", "phone", "email",
    "address", "city", "state", "zip_code", "insurance_provider",
    "insurance_policy_number", "insurance_group_number", "pcp_name",
    "pcp_contact", "status",
)


def _next_mrn(db: Database) -> str:
    row = db.query_one("SELECT COUNT(*) AS n FROM patients")
    return f"MRN{row['n'] + 1:06d}"


def _index_patient(db: Database, patient_id: int) -> None:
    row = db.query_one("SELECT * FROM patients WHERE id = ?", (patient_id,))
    if row is None:
        return
    title = f"{row['first_name']} {row['last_name']} ({row['mrn']})"
    content = " ".join(
        str(row[f]) for f in
        ("first_name", "last_name", "mrn", "phone", "email", "address",
         "insurance_provider", "pcp_name")
        if row[f]
    )
    search_dao.index_upsert(db, "patient", patient_id, patient_id, title, content)


def create_patient(db: Database, **fields) -> int:
    if not fields.get("first_name") or not fields.get("last_name") or not fields.get("dob"):
        raise ValueError("first_name, last_name and dob are required")
    if not fields.get("mrn"):
        fields["mrn"] = _next_mrn(db)
    # Fields left blank (None) are omitted so NOT NULL DEFAULT columns like
    # `status` fall back to their DB default instead of erroring out.
    cols = [f for f in PATIENT_FIELDS if f in fields and fields[f] is not None]
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO patients({', '.join(cols)}) VALUES ({placeholders})"
    patient_id = db.execute(sql, tuple(fields[c] for c in cols))
    _index_patient(db, patient_id)
    return patient_id


def update_patient(db: Database, patient_id: int, **fields) -> None:
    cols = [f for f in PATIENT_FIELDS if f in fields and fields[f] is not None]
    if not cols:
        return
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    sql = f"UPDATE patients SET {set_clause}, updated_at = datetime('now') WHERE id = ?"
    db.execute(sql, tuple(fields[c] for c in cols) + (patient_id,))
    _index_patient(db, patient_id)


def get_patient(db: Database, patient_id: int):
    return db.query_one("SELECT * FROM patients WHERE id = ?", (patient_id,))


def delete_patient(db: Database, patient_id: int) -> None:
    db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    search_dao.index_delete(db, "patient", patient_id)


def list_patients(db: Database, status: str | None = None) -> list:
    if status:
        return db.query(
            "SELECT * FROM patients WHERE status = ? ORDER BY last_name, first_name",
            (status,),
        )
    return db.query("SELECT * FROM patients ORDER BY last_name, first_name")


def search_patients(db: Database, term: str) -> list:
    """Fast patient search by name, MRN, phone, or email (QoL feature)."""
    like = f"%{term.strip()}%"
    return db.query(
        """
        SELECT * FROM patients
        WHERE first_name LIKE ? OR last_name LIKE ? OR mrn LIKE ?
           OR phone LIKE ? OR email LIKE ?
           OR (first_name || ' ' || last_name) LIKE ?
        ORDER BY last_name, first_name
        LIMIT 100
        """,
        (like, like, like, like, like, like),
    )


# ---------------------------------------------------------------- contacts
def add_emergency_contact(db: Database, patient_id: int, name: str, **fields) -> int:
    if not name:
        raise ValueError("Emergency contact name is required")
    return db.execute(
        "INSERT INTO emergency_contacts(patient_id, name, relationship, phone, email, address) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            patient_id, name, fields.get("relationship"), fields.get("phone"),
            fields.get("email"), fields.get("address"),
        ),
    )


def list_emergency_contacts(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM emergency_contacts WHERE patient_id = ? ORDER BY id", (patient_id,)
    )


def delete_emergency_contact(db: Database, contact_id: int) -> None:
    db.execute("DELETE FROM emergency_contacts WHERE id = ?", (contact_id,))


# ---------------------------------------------------------------- allergies
def add_allergy(
    db: Database, patient_id: int, substance: str, reaction: str = "",
    severity: str = "moderate", allergy_type: str = "drug", **fields
) -> int:
    if not substance:
        raise ValueError("Allergy substance is required")
    status = fields.get("status") or "active"  # column is NOT NULL DEFAULT 'active'
    allergy_id = db.execute(
        "INSERT INTO allergies(patient_id, substance, reaction, severity, allergy_type, "
        "status, noted_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, substance, reaction, severity, allergy_type,
            status, fields.get("noted_date"), fields.get("notes"),
        ),
    )
    _index_patient(db, patient_id)
    return allergy_id


def list_allergies(db: Database, patient_id: int, active_only: bool = False) -> list:
    if active_only:
        return db.query(
            "SELECT * FROM allergies WHERE patient_id = ? AND status = 'active' ORDER BY id",
            (patient_id,),
        )
    return db.query("SELECT * FROM allergies WHERE patient_id = ? ORDER BY id", (patient_id,))


def delete_allergy(db: Database, allergy_id: int) -> None:
    db.execute("DELETE FROM allergies WHERE id = ?", (allergy_id,))
