import pytest

from app.db.dao import patients


def test_create_and_get_patient(db):
    pid = patients.create_patient(db, first_name="John", last_name="Smith", dob="1990-01-01")
    row = patients.get_patient(db, pid)
    assert row["first_name"] == "John"
    assert row["mrn"].startswith("MRN")


def test_create_patient_requires_fields(db):
    with pytest.raises(ValueError):
        patients.create_patient(db, first_name="No", last_name="Dob")


def test_mrn_auto_increments(db):
    p1 = patients.create_patient(db, first_name="A", last_name="A", dob="2000-01-01")
    p2 = patients.create_patient(db, first_name="B", last_name="B", dob="2000-01-01")
    r1, r2 = patients.get_patient(db, p1), patients.get_patient(db, p2)
    assert r1["mrn"] != r2["mrn"]


def test_update_patient(db, patient_id):
    patients.update_patient(db, patient_id, phone="555-9999")
    row = patients.get_patient(db, patient_id)
    assert row["phone"] == "555-9999"


def test_search_patients_by_name(db, patient_id):
    results = patients.search_patients(db, "Jane")
    assert any(r["id"] == patient_id for r in results)


def test_search_patients_by_mrn(db, patient_id):
    row = patients.get_patient(db, patient_id)
    results = patients.search_patients(db, row["mrn"])
    assert len(results) == 1


def test_delete_patient_cascades_allergy(db, patient_id):
    patients.add_allergy(db, patient_id, "Penicillin", reaction="Rash")
    patients.delete_patient(db, patient_id)
    assert patients.get_patient(db, patient_id) is None
    assert patients.list_allergies(db, patient_id) == []


def test_emergency_contacts(db, patient_id):
    cid = patients.add_emergency_contact(db, patient_id, "John Doe", relationship="Spouse", phone="555-0000")
    contacts = patients.list_emergency_contacts(db, patient_id)
    assert len(contacts) == 1
    assert contacts[0]["name"] == "John Doe"
    patients.delete_emergency_contact(db, cid)
    assert patients.list_emergency_contacts(db, patient_id) == []


def test_emergency_contact_requires_name(db, patient_id):
    with pytest.raises(ValueError):
        patients.add_emergency_contact(db, patient_id, "")


def test_allergies_active_only_filter(db, patient_id):
    patients.add_allergy(db, patient_id, "Peanuts", severity="severe")
    a2 = patients.add_allergy(db, patient_id, "Latex", severity="mild", status="resolved")
    active = patients.list_allergies(db, patient_id, active_only=True)
    assert len(active) == 1
    assert active[0]["substance"] == "Peanuts"


def test_create_patient_blank_status_uses_default(db):
    """A GUI form that submits status=None (field left blank) must not
    violate the NOT NULL DEFAULT constraint on patients.status."""
    pid = patients.create_patient(db, first_name="No", last_name="Status", dob="1990-01-01", status=None)
    row = patients.get_patient(db, pid)
    assert row["status"] == "active"


def test_update_patient_blank_status_keeps_existing_value(db, patient_id):
    patients.update_patient(db, patient_id, status=None, phone="555-0001")
    row = patients.get_patient(db, patient_id)
    assert row["status"] == "active"
    assert row["phone"] == "555-0001"


def test_add_allergy_blank_status_uses_default(db, patient_id):
    allergy_id = patients.add_allergy(db, patient_id, "Bee stings", status=None)
    row = [a for a in patients.list_allergies(db, patient_id) if a["id"] == allergy_id][0]
    assert row["status"] == "active"


def test_list_patients_by_status(db):
    p1 = patients.create_patient(db, first_name="Active", last_name="One", dob="1990-01-01")
    p2 = patients.create_patient(db, first_name="Inactive", last_name="Two", dob="1990-01-01", status="inactive")
    active_list = patients.list_patients(db, status="active")
    assert any(p["id"] == p1 for p in active_list)
    assert not any(p["id"] == p2 for p in active_list)
