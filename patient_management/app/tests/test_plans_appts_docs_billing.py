import pytest

from app.db.dao import appointments, billing, documents, plans


def test_treatment_plan_and_overdue(db, patient_id):
    plans.create_plan(db, patient_id, therapy="Physical therapy", follow_up_date="2020-01-01")
    overdue = plans.overdue_follow_ups(db)
    assert any(p["patient_id"] == patient_id for p in overdue)


def test_treatment_plan_not_overdue_when_future(db, patient_id):
    plans.create_plan(db, patient_id, therapy="PT", follow_up_date="2099-01-01")
    overdue = plans.overdue_follow_ups(db)
    assert not any(p["patient_id"] == patient_id for p in overdue)


def test_treatment_plan_completed_excluded_from_overdue(db, patient_id):
    pid = plans.create_plan(db, patient_id, follow_up_date="2020-01-01")
    plans.update_plan(db, pid, status="completed")
    overdue = plans.overdue_follow_ups(db)
    assert not any(p["id"] == pid for p in overdue)


def test_schedule_and_status_appointment(db, patient_id):
    aid = appointments.schedule_appointment(db, patient_id, "2099-05-01 10:00", reason="Checkup")
    appointments.update_status(db, aid, "no-show")
    row = appointments.get_appointment(db, aid)
    assert row["status"] == "no-show"


def test_appointment_invalid_status(db, patient_id):
    aid = appointments.schedule_appointment(db, patient_id, "2099-05-01 10:00")
    with pytest.raises(ValueError):
        appointments.update_status(db, aid, "bogus")


def test_appointment_requires_datetime(db, patient_id):
    with pytest.raises(ValueError):
        appointments.schedule_appointment(db, patient_id, "")


def test_no_show_query(db, patient_id):
    aid = appointments.schedule_appointment(db, patient_id, "2020-01-01 09:00")
    appointments.update_status(db, aid, "no-show")
    rows = appointments.no_show_appointments(db, patient_id)
    assert len(rows) == 1


def test_documents_add_and_list(db, patient_id):
    did = documents.add_document(db, patient_id, "Discharge Summary", doc_type="discharge_summary")
    rows = documents.list_documents(db, patient_id)
    assert rows[0]["id"] == did


def test_document_requires_title(db, patient_id):
    with pytest.raises(ValueError):
        documents.add_document(db, patient_id, "")


def test_store_file_copies_into_data_dir(db, patient_id, tmp_path):
    src = tmp_path / "consent.txt"
    src.write_text("consent form contents")
    stored_path = documents.store_file(src)
    assert stored_path != str(src)
    from pathlib import Path
    assert Path(stored_path).exists()
    assert Path(stored_path).read_text() == "consent form contents"


def test_store_file_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        documents.store_file(tmp_path / "does_not_exist.txt")


def test_billing_claim_and_invoice_payment_flow(db, patient_id):
    billing.create_claim(db, patient_id, amount_billed=200, insurance_provider="Acme Health")
    inv_id = billing.create_invoice(db, patient_id, amount_due=100)
    billing.record_payment(db, inv_id, patient_id, 60)
    invoices = billing.list_invoices(db, patient_id)
    assert invoices[0]["amount_paid"] == 60
    assert invoices[0]["status"] == "open"
    billing.record_payment(db, inv_id, patient_id, 40)
    invoices = billing.list_invoices(db, patient_id)
    assert invoices[0]["status"] == "paid"


def test_negative_invoice_amount_rejected(db, patient_id):
    with pytest.raises(ValueError):
        billing.create_invoice(db, patient_id, amount_due=-5)


def test_payment_must_be_positive(db, patient_id):
    inv_id = billing.create_invoice(db, patient_id, amount_due=100)
    with pytest.raises(ValueError):
        billing.record_payment(db, inv_id, patient_id, 0)


def test_balance_due(db, patient_id):
    billing.create_invoice(db, patient_id, amount_due=150)
    balance = billing.balance_due(db, patient_id)
    assert balance == 150
