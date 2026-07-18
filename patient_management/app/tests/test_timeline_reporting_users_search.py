import pytest

from app.db.dao import (
    audit, diagnoses, orders, patients, prescriptions, reporting, search, templates,
    timeline, users, visits,
)


def test_timeline_aggregates_events(db, patient_id):
    visits.create_visit(db, patient_id, visit_date="2024-01-01", chief_complaint="Checkup")
    diagnoses.add_diagnosis(db, patient_id, "I10", "Hypertension", onset_date="2024-01-01")
    prescriptions.create_prescription(db, patient_id, "Lisinopril", start_date="2024-01-01")
    events = timeline.get_timeline(db, patient_id)
    types = {e["type"] for e in events}
    assert {"visit", "diagnosis", "prescription"} <= types


def test_timeline_sorted_descending(db, patient_id):
    visits.create_visit(db, patient_id, visit_date="2024-01-01", chief_complaint="Old")
    visits.create_visit(db, patient_id, visit_date="2024-06-01", chief_complaint="New")
    events = timeline.get_timeline(db, patient_id)
    visit_events = [e for e in events if e["type"] == "visit"]
    assert visit_events[0]["timestamp"] >= visit_events[1]["timestamp"]


def test_patient_summary_report(db, patient_id):
    diagnoses.add_diagnosis(db, patient_id, "E11.9", "Diabetes")
    prescriptions.create_prescription(db, patient_id, "Metformin")
    patients.add_allergy(db, patient_id, "Sulfa")
    summary = reporting.patient_summary(db, patient_id)
    assert summary["patient"]["id"] == patient_id
    assert len(summary["active_problems"]) == 1
    assert len(summary["active_medications"]) == 1
    assert len(summary["allergies"]) == 1


def test_patient_summary_missing_patient_raises(db):
    with pytest.raises(ValueError):
        reporting.patient_summary(db, 99999)


def test_clinic_statistics_runs(db, patient_id):
    visits.create_visit(db, patient_id, chief_complaint="X")
    stats = reporting.clinic_statistics(db)
    assert stats["total_patients"] >= 1
    assert stats["total_visits"] >= 1


def test_disease_registry(db, patient_id):
    diagnoses.add_diagnosis(db, patient_id, "E11.9", "Type 2 diabetes")
    registry = reporting.disease_registry(db, icd_code="E11.9")
    assert len(registry) == 1
    assert registry[0]["id"] == patient_id


def test_user_creation_and_auth(db):
    users.create_user(db, "drsmith", "SecurePass1!", "Dr. Smith", role="physician")
    result = users.authenticate(db, "drsmith", "SecurePass1!")
    assert result.success is True
    assert result.user["role"] == "physician"


def test_user_auth_wrong_password(db):
    users.create_user(db, "nurse1", "pass123", "Nurse One", role="nurse")
    result = users.authenticate(db, "nurse1", "wrongpass")
    assert result.success is False


def test_user_auth_unknown_user(db):
    result = users.authenticate(db, "ghost", "whatever")
    assert result.success is False


def test_duplicate_username_rejected(db):
    users.create_user(db, "dup", "pass1", "First")
    with pytest.raises(Exception):
        users.create_user(db, "dup", "pass2", "Second")


def test_invalid_role_rejected(db):
    with pytest.raises(ValueError):
        users.create_user(db, "someone", "pass", "Someone", role="not_a_role")


def test_ensure_default_admin_creates_once(db):
    users.ensure_default_admin(db)
    users.ensure_default_admin(db)
    all_users = users.list_users(db)
    assert len(all_users) == 1
    assert all_users[0]["username"] == "admin"


def test_audit_log_records_action(db):
    audit.log_action(db, "LOGIN", username="admin")
    logs = audit.list_audit_log(db)
    assert logs[0]["action"] == "LOGIN"


def test_templates_crud(db):
    tid = templates.create_template(db, "Diabetes Follow-up", "visit_note", {"plan": "Check A1c"})
    fetched = templates.get_template(db, tid)
    assert fetched["content"]["plan"] == "Check A1c"
    templates.delete_template(db, tid)
    assert templates.get_template(db, tid) is None


def test_autosave_draft_and_versions(db, patient_id):
    templates.save_draft(db, "visit", None, patient_id, {"hpi": "draft text v1"})
    templates.save_draft(db, "visit", None, patient_id, {"hpi": "draft text v2"})
    latest = templates.latest_draft(db, "visit", None)
    assert latest["content"]["hpi"] == "draft text v2"
    versions = templates.list_versions(db, "visit", None)
    assert len(versions) == 2
    assert versions[0]["content"]["hpi"] == "draft text v2"


def test_full_text_search_finds_patient(db, patient_id):
    results = search.full_text_search(db, "Jane")
    assert any(r["entity_type"] == "patient" for r in results)


def test_full_text_search_finds_visit_note(db, patient_id):
    visits.create_visit(db, patient_id, chief_complaint="Severe migraine headache")
    results = search.full_text_search(db, "migraine")
    assert any(r["entity_type"] == "visit" for r in results)


def test_full_text_search_empty_query(db):
    assert search.full_text_search(db, "   ") == []


def test_search_index_removed_on_delete(db, patient_id):
    diag_id = diagnoses.add_diagnosis(db, patient_id, "R51", "Headache")
    assert search.full_text_search(db, "Headache")
    diagnoses.delete_diagnosis(db, diag_id)
    results = search.full_text_search(db, "Headache")
    assert not any(r["entity_type"] == "diagnosis" and r["entity_id"] == diag_id for r in results)
