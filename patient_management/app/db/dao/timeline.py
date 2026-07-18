"""Module 11: Clinical Timeline — chronological aggregation of visits,
diagnoses, medications, orders/results and appointments for one patient."""
from __future__ import annotations

from app.db.database import Database


def get_timeline(db: Database, patient_id: int) -> list[dict]:
    events: list[dict] = []

    for row in db.query(
        "SELECT id, visit_date AS ts, visit_type, chief_complaint FROM visits "
        "WHERE patient_id = ?", (patient_id,)
    ):
        events.append({
            "timestamp": row["ts"], "type": "visit", "id": row["id"],
            "summary": f"{row['visit_type']}: {row['chief_complaint'] or ''}".strip(": "),
        })

    for row in db.query(
        "SELECT id, onset_date AS ts, icd_code, description FROM diagnoses "
        "WHERE patient_id = ? AND onset_date IS NOT NULL", (patient_id,)
    ):
        events.append({
            "timestamp": row["ts"], "type": "diagnosis", "id": row["id"],
            "summary": f"{row['icd_code']} - {row['description']}",
        })

    for row in db.query(
        "SELECT id, start_date AS ts, medication_name, dosage FROM prescriptions "
        "WHERE patient_id = ?", (patient_id,)
    ):
        events.append({
            "timestamp": row["ts"], "type": "prescription", "id": row["id"],
            "summary": f"Prescribed {row['medication_name']} {row['dosage'] or ''}".strip(),
        })

    for row in db.query(
        "SELECT id, ordered_date AS ts, order_type, order_name, status FROM orders "
        "WHERE patient_id = ?", (patient_id,)
    ):
        events.append({
            "timestamp": row["ts"], "type": "order", "id": row["id"],
            "summary": f"{row['order_type'].title()} order: {row['order_name']} ({row['status']})",
        })

    for row in db.query(
        "SELECT id, result_date AS ts, result_name, value, abnormal_flag FROM results "
        "WHERE patient_id = ?", (patient_id,)
    ):
        flag = f" [{row['abnormal_flag'].upper()}]" if row["abnormal_flag"] not in (None, "normal", "unknown") else ""
        events.append({
            "timestamp": row["ts"], "type": "result", "id": row["id"],
            "summary": f"Result {row['result_name']}: {row['value']}{flag}",
        })

    for row in db.query(
        "SELECT id, appt_datetime AS ts, reason, status FROM appointments "
        "WHERE patient_id = ?", (patient_id,)
    ):
        events.append({
            "timestamp": row["ts"], "type": "appointment", "id": row["id"],
            "summary": f"Appointment ({row['status']}): {row['reason'] or ''}".strip(": "),
        })

    events.sort(key=lambda e: e["timestamp"] or "", reverse=True)
    return events
