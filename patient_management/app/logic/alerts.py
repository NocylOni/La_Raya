"""Aggregated clinical alerts: drug interactions, allergy conflicts,
abnormal labs, overdue follow-ups (QoL: clinical alerts)."""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import orders as orders_dao
from app.db.dao import patients as patients_dao
from app.db.dao import prescriptions as prescriptions_dao
from app.db.dao import plans as plans_dao
from app.logic import interactions


def check_new_prescription(db: Database, patient_id: int, medication_name: str) -> dict:
    """Call before saving a new prescription to surface interaction/allergy
    alerts. Does not block saving — the GUI decides whether to warn/confirm."""
    active_rx = prescriptions_dao.list_prescriptions(db, patient_id, active_only=True)
    active_names = [r["medication_name"] for r in active_rx]
    interaction_alerts = interactions.check_drug_interactions(medication_name, active_names)

    allergies = [dict(a) for a in patients_dao.list_allergies(db, patient_id, active_only=True)]
    allergy_alerts = interactions.check_allergy_conflict(medication_name, allergies)

    return {
        "interactions": interaction_alerts,
        "allergy_conflicts": allergy_alerts,
        "has_alerts": bool(interaction_alerts or allergy_alerts),
    }


def patient_alerts(db: Database, patient_id: int) -> dict:
    """All standing alerts for a single patient's dashboard."""
    abnormal = orders_dao.abnormal_results(db, patient_id)
    overdue = [p for p in plans_dao.overdue_follow_ups(db) if p["patient_id"] == patient_id]

    active_rx = prescriptions_dao.list_prescriptions(db, patient_id, active_only=True)
    names = [r["medication_name"] for r in active_rx]
    seen = set()
    cross_interactions = []
    for i, med in enumerate(names):
        for other in names[i + 1:]:
            hits = interactions.check_drug_interactions(med, [other])
            for hit in hits:
                key = tuple(sorted((hit["drug_a"], hit["drug_b"])))
                if key not in seen:
                    seen.add(key)
                    cross_interactions.append(hit)

    return {
        "abnormal_results": [dict(r) for r in abnormal],
        "overdue_follow_ups": overdue,
        "current_medication_interactions": cross_interactions,
    }


def clinic_wide_alerts(db: Database) -> dict:
    """Alerts across the whole clinic for a dashboard/home screen."""
    overdue = plans_dao.overdue_follow_ups(db)
    recent_abnormal = db.query(
        "SELECT r.*, p.first_name, p.last_name, p.mrn FROM results r "
        "JOIN patients p ON p.id = r.patient_id "
        "WHERE r.abnormal_flag IN ('high', 'low', 'critical') "
        "ORDER BY r.result_date DESC LIMIT 25"
    )
    return {
        "overdue_follow_ups": [dict(r) for r in overdue],
        "recent_abnormal_results": [dict(r) for r in recent_abnormal],
    }
