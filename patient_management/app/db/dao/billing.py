"""Module 10: Billing & Administration (claims, invoices, payments, coding)."""
from __future__ import annotations

from app.db.database import Database


# --------------------------------------------------------------- claims
def create_claim(db: Database, patient_id: int, visit_id: int | None = None, **fields) -> int:
    return db.execute(
        "INSERT INTO billing_claims(patient_id, visit_id, claim_date, insurance_provider, "
        "cpt_codes, icd_codes, amount_billed, amount_paid, status, notes) "
        "VALUES (?, ?, COALESCE(?, date('now')), ?, ?, ?, ?, ?, ?, ?)",
        (
            patient_id, visit_id, fields.get("claim_date"), fields.get("insurance_provider"),
            fields.get("cpt_codes"), fields.get("icd_codes"), fields.get("amount_billed", 0),
            fields.get("amount_paid", 0), fields.get("status", "submitted"), fields.get("notes"),
        ),
    )


def update_claim_status(db: Database, claim_id: int, status: str, amount_paid: float | None = None) -> None:
    if amount_paid is not None:
        db.execute(
            "UPDATE billing_claims SET status = ?, amount_paid = ? WHERE id = ?",
            (status, amount_paid, claim_id),
        )
    else:
        db.execute("UPDATE billing_claims SET status = ? WHERE id = ?", (status, claim_id))


def list_claims(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM billing_claims WHERE patient_id = ? ORDER BY claim_date DESC",
        (patient_id,),
    )


# -------------------------------------------------------------- invoices
def create_invoice(db: Database, patient_id: int, amount_due: float, **fields) -> int:
    if amount_due < 0:
        raise ValueError("amount_due cannot be negative")
    return db.execute(
        "INSERT INTO invoices(patient_id, invoice_date, amount_due, amount_paid, status, "
        "due_date, notes) VALUES (?, COALESCE(?, date('now')), ?, ?, ?, ?, ?)",
        (
            patient_id, fields.get("invoice_date"), amount_due, fields.get("amount_paid", 0),
            fields.get("status", "open"), fields.get("due_date"), fields.get("notes"),
        ),
    )


def record_payment(
    db: Database, invoice_id: int, patient_id: int, amount: float, method: str = "cash",
    **fields
) -> int:
    if amount <= 0:
        raise ValueError("Payment amount must be positive")
    payment_id = db.execute(
        "INSERT INTO payments(invoice_id, patient_id, payment_date, amount, method, notes) "
        "VALUES (?, ?, COALESCE(?, date('now')), ?, ?, ?)",
        (invoice_id, patient_id, fields.get("payment_date"), amount, method, fields.get("notes")),
    )
    invoice = db.query_one("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    if invoice is not None:
        new_paid = invoice["amount_paid"] + amount
        status = "paid" if new_paid >= invoice["amount_due"] else invoice["status"]
        db.execute(
            "UPDATE invoices SET amount_paid = ?, status = ? WHERE id = ?",
            (new_paid, status, invoice_id),
        )
    return payment_id


def list_invoices(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM invoices WHERE patient_id = ? ORDER BY invoice_date DESC", (patient_id,)
    )


def list_payments(db: Database, invoice_id: int) -> list:
    return db.query("SELECT * FROM payments WHERE invoice_id = ? ORDER BY payment_date", (invoice_id,))


def overdue_invoices(db: Database) -> list:
    return db.query(
        "SELECT i.*, p.first_name, p.last_name, p.mrn FROM invoices i "
        "JOIN patients p ON p.id = i.patient_id "
        "WHERE i.status != 'paid' AND i.status != 'void' AND i.due_date IS NOT NULL "
        "AND date(i.due_date) < date('now') ORDER BY i.due_date"
    )


def balance_due(db: Database, patient_id: int) -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(amount_due - amount_paid), 0) AS balance FROM invoices "
        "WHERE patient_id = ? AND status != 'void'",
        (patient_id,),
    )
    return row["balance"]
