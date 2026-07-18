import pytest

from app.db.dao import history, visits


def test_add_history_item(db, patient_id):
    hid = history.add_history_item(db, patient_id, "past_medical", "Appendectomy 2010")
    items = history.list_history(db, patient_id, category="past_medical")
    assert len(items) == 1
    assert items[0]["id"] == hid


def test_invalid_history_category(db, patient_id):
    with pytest.raises(ValueError):
        history.add_history_item(db, patient_id, "not_a_category", "x")


def test_immunizations(db, patient_id):
    history.add_immunization(db, patient_id, "Influenza", date_given="2024-10-01")
    items = history.list_immunizations(db, patient_id)
    assert len(items) == 1


def test_medication_history(db, patient_id):
    history.add_medication_history(db, patient_id, "Metformin", dosage="500mg", status="discontinued")
    items = history.list_medication_history(db, patient_id)
    assert items[0]["name"] == "Metformin"


def test_create_visit_and_soap_fields(db, patient_id):
    vid = visits.create_visit(
        db, patient_id, chief_complaint="Cough", hpi="3 days of cough",
        assessment="URI", plan="Rest and fluids",
    )
    visit = visits.get_visit(db, vid)
    assert visit["chief_complaint"] == "Cough"
    assert visit["assessment"] == "URI"


def test_update_visit(db, patient_id):
    vid = visits.create_visit(db, patient_id, chief_complaint="Headache")
    visits.update_visit(db, vid, plan="Tylenol")
    visit = visits.get_visit(db, vid)
    assert visit["plan"] == "Tylenol"


def test_record_vitals_computes_bmi(db, patient_id):
    vitals_id = visits.record_vitals(db, patient_id, height_cm=170, weight_kg=70)
    rows = visits.list_vitals(db, patient_id)
    assert len(rows) == 1
    assert rows[0]["bmi"] == pytest.approx(24.2, abs=0.1)


def test_record_vitals_no_height_weight_no_bmi(db, patient_id):
    visits.record_vitals(db, patient_id, heart_rate=72)
    rows = visits.list_vitals(db, patient_id)
    assert rows[0]["bmi"] is None


def test_create_visit_blank_visit_date_uses_default(db, patient_id):
    """A GUI form submitting visit_date=None must not violate the NOT NULL
    DEFAULT constraint on visits.visit_date."""
    vid = visits.create_visit(db, patient_id, visit_date=None, chief_complaint="Blank date")
    visit = visits.get_visit(db, vid)
    assert visit["visit_date"] is not None


def test_update_visit_blank_visit_date_keeps_existing_value(db, patient_id):
    vid = visits.create_visit(db, patient_id, visit_date="2024-01-01", chief_complaint="X")
    visits.update_visit(db, vid, visit_date=None, plan="Updated plan")
    visit = visits.get_visit(db, vid)
    assert visit["visit_date"] == "2024-01-01"
    assert visit["plan"] == "Updated plan"


def test_list_visits_ordered_desc(db, patient_id):
    visits.create_visit(db, patient_id, visit_date="2024-01-01", chief_complaint="First")
    visits.create_visit(db, patient_id, visit_date="2024-06-01", chief_complaint="Second")
    rows = visits.list_visits(db, patient_id)
    assert rows[0]["chief_complaint"] == "Second"
