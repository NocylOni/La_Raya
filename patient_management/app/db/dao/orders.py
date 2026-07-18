"""Module 5: Orders & Results (labs, imaging, procedures, pathology)."""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import search as search_dao

ORDER_TYPES = ("lab", "imaging", "procedure", "pathology")


def create_order(
    db: Database, patient_id: int, order_type: str, order_name: str,
    visit_id: int | None = None, **fields
) -> int:
    if order_type not in ORDER_TYPES:
        raise ValueError(f"Unknown order type: {order_type}")
    if not order_name:
        raise ValueError("order_name is required")
    return db.execute(
        "INSERT INTO orders(patient_id, visit_id, order_type, order_name, ordered_date, "
        "status, ordered_by, notes) VALUES (?, ?, ?, ?, COALESCE(?, datetime('now')), ?, ?, ?)",
        (
            patient_id, visit_id, order_type, order_name, fields.get("ordered_date"),
            fields.get("status", "ordered"), fields.get("ordered_by"), fields.get("notes"),
        ),
    )


def update_order_status(db: Database, order_id: int, status: str) -> None:
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


def get_order(db: Database, order_id: int):
    return db.query_one("SELECT * FROM orders WHERE id = ?", (order_id,))


def list_orders(db: Database, patient_id: int, order_type: str | None = None) -> list:
    if order_type:
        return db.query(
            "SELECT * FROM orders WHERE patient_id = ? AND order_type = ? "
            "ORDER BY ordered_date DESC",
            (patient_id, order_type),
        )
    return db.query(
        "SELECT * FROM orders WHERE patient_id = ? ORDER BY ordered_date DESC", (patient_id,)
    )


def delete_order(db: Database, order_id: int) -> None:
    db.execute("DELETE FROM orders WHERE id = ?", (order_id,))


# --------------------------------------------------------------- results
def _compute_abnormal_flag(
    numeric_value: float | None, reference_low: float | None, reference_high: float | None
) -> str:
    if numeric_value is None or (reference_low is None and reference_high is None):
        return "unknown"
    if reference_low is not None and numeric_value < reference_low:
        return "low"
    if reference_high is not None and numeric_value > reference_high:
        return "high"
    return "normal"


def add_result(
    db: Database, order_id: int, patient_id: int, result_name: str, **fields
) -> int:
    if not result_name:
        raise ValueError("result_name is required")
    numeric_value = fields.get("numeric_value")
    reference_low = fields.get("reference_low")
    reference_high = fields.get("reference_high")
    flag = fields.get("abnormal_flag") or _compute_abnormal_flag(
        numeric_value, reference_low, reference_high
    )
    result_id = db.execute(
        "INSERT INTO results(order_id, patient_id, result_name, value, numeric_value, unit, "
        "reference_low, reference_high, abnormal_flag, result_date, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now')), ?)",
        (
            order_id, patient_id, result_name, fields.get("value"), numeric_value,
            fields.get("unit"), reference_low, reference_high, flag,
            fields.get("result_date"), fields.get("notes"),
        ),
    )
    search_dao.index_upsert(
        db, "result", result_id, patient_id, result_name,
        f"{fields.get('value', '')} {fields.get('unit', '')} {fields.get('notes', '')}",
    )
    return result_id


def list_results(db: Database, patient_id: int, order_id: int | None = None) -> list:
    if order_id:
        return db.query(
            "SELECT * FROM results WHERE order_id = ? ORDER BY result_date", (order_id,)
        )
    return db.query(
        "SELECT * FROM results WHERE patient_id = ? ORDER BY result_date DESC", (patient_id,)
    )


def result_trend(db: Database, patient_id: int, result_name: str) -> list:
    """Chronological trend of a single result type (QoL: graphs for lab trends)."""
    return db.query(
        "SELECT * FROM results WHERE patient_id = ? AND result_name = ? "
        "ORDER BY result_date",
        (patient_id, result_name),
    )


def abnormal_results(db: Database, patient_id: int) -> list:
    return db.query(
        "SELECT * FROM results WHERE patient_id = ? AND abnormal_flag IN ('high', 'low', "
        "'critical') ORDER BY result_date DESC",
        (patient_id,),
    )


def delete_result(db: Database, result_id: int) -> None:
    db.execute("DELETE FROM results WHERE id = ?", (result_id,))
    search_dao.index_delete(db, "result", result_id)
