import pytest

from app.db.dao import diagnoses, orders, prescriptions


def test_add_diagnosis_and_problem_list(db, patient_id):
    diagnoses.add_diagnosis(db, patient_id, "E11.9", "Type 2 diabetes", chronic=True, onset_date="2020-01-01")
    diagnoses.add_diagnosis(db, patient_id, "J06.9", "URI", status="resolved")
    problems = diagnoses.problem_list(db, patient_id)
    assert len(problems) == 1
    assert problems[0]["icd_code"] == "E11.9"


def test_chronic_conditions(db, patient_id):
    diagnoses.add_diagnosis(db, patient_id, "I10", "Hypertension", chronic=True)
    chronic = diagnoses.chronic_conditions(db, patient_id)
    assert len(chronic) == 1


def test_update_diagnosis_status(db, patient_id):
    did = diagnoses.add_diagnosis(db, patient_id, "R51", "Headache")
    diagnoses.update_diagnosis(db, did, status="resolved", resolved_date="2024-01-01")
    row = diagnoses.get_diagnosis(db, did)
    assert row["status"] == "resolved"


def test_diagnosis_requires_code_and_description(db, patient_id):
    with pytest.raises(ValueError):
        diagnoses.add_diagnosis(db, patient_id, "", "")


def test_create_order_invalid_type(db, patient_id):
    with pytest.raises(ValueError):
        orders.create_order(db, patient_id, "not_a_type", "CBC")


def test_order_and_result_abnormal_flag_high(db, patient_id):
    oid = orders.create_order(db, patient_id, "lab", "Glucose Panel")
    orders.add_result(
        db, oid, patient_id, "Glucose", numeric_value=180, unit="mg/dL",
        reference_low=70, reference_high=99,
    )
    results = orders.list_results(db, patient_id)
    assert results[0]["abnormal_flag"] == "high"


def test_order_and_result_normal_flag(db, patient_id):
    oid = orders.create_order(db, patient_id, "lab", "Glucose Panel")
    orders.add_result(
        db, oid, patient_id, "Glucose", numeric_value=85, unit="mg/dL",
        reference_low=70, reference_high=99,
    )
    results = orders.list_results(db, patient_id)
    assert results[0]["abnormal_flag"] == "normal"


def test_result_trend(db, patient_id):
    oid = orders.create_order(db, patient_id, "lab", "A1C")
    orders.add_result(db, oid, patient_id, "HbA1c", numeric_value=6.1, result_date="2024-01-01")
    orders.add_result(db, oid, patient_id, "HbA1c", numeric_value=6.5, result_date="2024-06-01")
    trend = orders.result_trend(db, patient_id, "HbA1c")
    assert [r["numeric_value"] for r in trend] == [6.1, 6.5]


def test_abnormal_results_query(db, patient_id):
    oid = orders.create_order(db, patient_id, "lab", "Chem Panel")
    orders.add_result(db, oid, patient_id, "Potassium", numeric_value=6.2, reference_low=3.5, reference_high=5.1)
    orders.add_result(db, oid, patient_id, "Sodium", numeric_value=140, reference_low=135, reference_high=145)
    abnormal = orders.abnormal_results(db, patient_id)
    assert len(abnormal) == 1
    assert abnormal[0]["result_name"] == "Potassium"


def test_create_prescription_and_refill(db, patient_id):
    rx_id = prescriptions.create_prescription(
        db, patient_id, "Lisinopril", dosage="10mg", frequency="daily", refills=2,
    )
    ok = prescriptions.refill_prescription(db, rx_id)
    assert ok is True
    row = prescriptions.get_prescription(db, rx_id)
    assert row["refills_remaining"] == 1


def test_refill_exhausted(db, patient_id):
    rx_id = prescriptions.create_prescription(db, patient_id, "Amoxicillin", refills=0)
    ok = prescriptions.refill_prescription(db, rx_id)
    assert ok is False


def test_list_active_prescriptions(db, patient_id):
    prescriptions.create_prescription(db, patient_id, "DrugA", status="active")
    prescriptions.create_prescription(db, patient_id, "DrugB", status="completed")
    active = prescriptions.list_prescriptions(db, patient_id, active_only=True)
    assert len(active) == 1
    assert active[0]["medication_name"] == "DrugA"
