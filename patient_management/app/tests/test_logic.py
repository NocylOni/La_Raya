from pathlib import Path

from app.db.dao import orders, patients, plans, prescriptions
from app.logic import alerts, interactions, pdf_export, reference_ranges


def test_drug_interaction_detected():
    hits = interactions.check_drug_interactions("Warfarin", ["Aspirin 81mg"])
    assert len(hits) == 1
    assert hits[0]["severity"] == "major"


def test_drug_interaction_none_when_unrelated():
    hits = interactions.check_drug_interactions("Amoxicillin", ["Lisinopril"])
    assert hits == []


def test_allergy_conflict_detected():
    allergies = [{"substance": "Penicillin", "severity": "severe"}]
    hits = interactions.check_allergy_conflict("Amoxicillin-Penicillin combo", allergies)
    assert len(hits) == 1


def test_allergy_conflict_none():
    allergies = [{"substance": "Peanuts", "severity": "severe"}]
    hits = interactions.check_allergy_conflict("Ibuprofen", allergies)
    assert hits == []


def test_check_new_prescription_flags_interaction(db, patient_id):
    prescriptions.create_prescription(db, patient_id, "Warfarin", status="active")
    result = alerts.check_new_prescription(db, patient_id, "Aspirin")
    assert result["has_alerts"] is True
    assert len(result["interactions"]) == 1


def test_check_new_prescription_flags_allergy(db, patient_id):
    patients.add_allergy(db, patient_id, "Sulfa", severity="severe")
    result = alerts.check_new_prescription(db, patient_id, "Sulfamethoxazole")
    assert result["has_alerts"] is True
    assert len(result["allergy_conflicts"]) == 1


def test_check_new_prescription_no_alerts(db, patient_id):
    result = alerts.check_new_prescription(db, patient_id, "Vitamin D")
    assert result["has_alerts"] is False


def test_patient_alerts_includes_abnormal_and_overdue(db, patient_id):
    oid = orders.create_order(db, patient_id, "lab", "Potassium")
    orders.add_result(db, oid, patient_id, "Potassium", numeric_value=6.5,
                       reference_low=3.5, reference_high=5.1)
    plans.create_plan(db, patient_id, follow_up_date="2020-01-01")
    result = alerts.patient_alerts(db, patient_id)
    assert len(result["abnormal_results"]) == 1
    assert len(result["overdue_follow_ups"]) == 1


def test_clinic_wide_alerts_runs(db, patient_id):
    result = alerts.clinic_wide_alerts(db)
    assert "overdue_follow_ups" in result
    assert "recent_abnormal_results" in result


def test_lookup_reference_range():
    r = reference_ranges.lookup_reference_range("Glucose")
    assert r is not None
    assert r[0] == 70


def test_flag_vital_high():
    assert reference_ranges.flag_vital("heart_rate", 140) == "high"


def test_flag_vital_normal():
    assert reference_ranges.flag_vital("heart_rate", 72) == "normal"


def test_export_patient_summary_pdf(db, patient_id, tmp_path):
    out = tmp_path / "summary.pdf"
    result_path = pdf_export.export_patient_summary_pdf(db, patient_id, out)
    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0


def test_export_visit_note_pdf(db, patient_id, tmp_path):
    from app.db.dao import visits
    vid = visits.create_visit(db, patient_id, chief_complaint="Cough", plan="Rest")
    out = tmp_path / "visit.pdf"
    result_path = pdf_export.export_visit_note_pdf(db, vid, out)
    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0
