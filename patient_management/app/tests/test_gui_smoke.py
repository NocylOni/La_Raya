"""Headless GUI smoke test (requires a display, e.g. via xvfb-run).

Exercises the real Tkinter widget tree end to end: login, patient creation,
every tab's load_patient(), and one create-record round trip per tab. This
catches Tkinter wiring bugs (bad widget references, callback signature
mismatches) that the pure DAO unit tests can't see.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox

import pytest

if not os.environ.get("DISPLAY"):
    pytest.skip("No DISPLAY available for GUI smoke test", allow_module_level=True)

from app.db.dao import users as users_dao
from app.gui.main_window import MainWindow


@pytest.fixture(autouse=True)
def no_blocking_dialogs(monkeypatch):
    """messagebox popups block on a real display waiting for a click that
    will never come in an automated test - stub them out."""
    monkeypatch.setattr(messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "showerror", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "showwarning", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)


@pytest.fixture()
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture()
def logged_in_user(db):
    users_dao.create_user(db, "smoketest", "pw12345", "Smoke Test", role="admin")
    result = users_dao.authenticate(db, "smoketest", "pw12345")
    assert result.success
    return result.user


def test_main_window_builds_all_tabs(root, db, logged_in_user):
    win = MainWindow(root, db, logged_in_user)
    root.update()
    tab_labels = [win.notebook.tab(i, "text") for i in range(len(win.notebook.tabs()))]
    expected = {
        "Dashboard", "Patient Registry", "Medical History", "Visits / SOAP", "Vitals",
        "Diagnoses", "Orders & Results", "Prescriptions", "Treatment Plan", "Appointments",
        "Documents", "Billing", "Clinical Timeline", "Reporting & Analytics", "Admin",
    }
    assert expected <= set(tab_labels)


def test_create_patient_via_registry_tab(root, db, logged_in_user):
    win = MainWindow(root, db, logged_in_user)
    root.update()
    registry = win._tab_instances["Patient Registry"]
    registry._entries["first_name"].insert(0, "Alice")
    registry._entries["last_name"].insert(0, "Wonder")
    registry._entries["dob"].insert(0, "1992-02-02")
    registry._save_demographics()
    root.update()
    assert win.current_patient_id is not None


def test_full_workflow_across_tabs(root, db, logged_in_user):
    """Create a patient, then add one record through every module tab,
    exercising the RecordPanel widgets exactly as a user would."""
    win = MainWindow(root, db, logged_in_user)
    root.update()

    registry = win._tab_instances["Patient Registry"]
    registry._entries["first_name"].insert(0, "Bob")
    registry._entries["last_name"].insert(0, "Builder")
    registry._entries["dob"].insert(0, "1980-05-05")
    registry._save_demographics()
    root.update()
    assert win.current_patient_id is not None

    # Allergies (nested RecordPanel inside Registry tab)
    allergy_panel = registry.allergy_panel
    allergy_panel._widgets["substance"].insert(0, "Penicillin")
    allergy_panel._widgets["severity"].set("severe")
    allergy_panel._save()
    root.update()
    assert len(allergy_panel._records) == 1

    # Medical History
    history = win._tab_instances["Medical History"]
    past_medical_panel = history.panels[0]
    past_medical_panel._widgets["description"].insert("1.0", "Hypertension diagnosed 2015")
    past_medical_panel._save()
    root.update()
    assert len(past_medical_panel._records) == 1

    # Visits (SOAP)
    visits = win._tab_instances["Visits / SOAP"]
    visits.panel._widgets["chief_complaint"].insert(0, "Annual checkup")
    visits.panel._widgets["visit_type"].set("annual physical")
    visits.panel._save()
    root.update()
    assert len(visits.panel._records) == 1

    # Vitals
    vitals = win._tab_instances["Vitals"]
    vitals.panel._widgets["heart_rate"].insert(0, "72")
    vitals.panel._widgets["height_cm"].insert(0, "180")
    vitals.panel._widgets["weight_kg"].insert(0, "80")
    vitals.panel._save()
    root.update()
    assert len(vitals.panel._records) == 1

    # Diagnoses
    diagnoses = win._tab_instances["Diagnoses"]
    diagnoses.panel._widgets["icd_code"].insert(0, "I10")
    diagnoses.panel._widgets["description"].insert(0, "Essential hypertension")
    diagnoses.panel._save()
    root.update()
    assert len(diagnoses.panel._records) == 1

    # Orders & Results
    orders_tab = win._tab_instances["Orders & Results"]
    orders_tab.orders_panel._widgets["order_type"].set("lab")
    orders_tab.orders_panel._widgets["order_name"].insert(0, "Basic Metabolic Panel")
    orders_tab.orders_panel._save()
    root.update()
    assert len(orders_tab.orders_panel._records) == 1
    first_order_id = next(iter(orders_tab.orders_panel._records))
    orders_tab.orders_panel.tree.selection_set(str(first_order_id))
    orders_tab.orders_panel.tree.event_generate("<<TreeviewSelect>>")
    root.update()
    orders_tab.results_panel._widgets["result_name"].insert(0, "Sodium")
    orders_tab.results_panel._widgets["numeric_value"].insert(0, "140")
    orders_tab.results_panel._widgets["reference_low"].insert(0, "135")
    orders_tab.results_panel._widgets["reference_high"].insert(0, "145")
    orders_tab.results_panel._save()
    root.update()
    assert len(orders_tab.results_panel._records) == 1

    # Prescriptions (with allergy alert path exercised separately in DAO tests)
    rx = win._tab_instances["Prescriptions"]
    rx.panel._widgets["medication_name"].insert(0, "Lisinopril")
    rx.panel._widgets["dosage"].insert(0, "10mg")
    rx.panel._save()
    root.update()
    assert len(rx.panel._records) == 1

    # Treatment Plan
    plans = win._tab_instances["Treatment Plan"]
    plans.panel._widgets["therapy"].insert(0, "Lifestyle modification")
    plans.panel._save()
    root.update()
    assert len(plans.panel._records) == 1

    # Appointments
    appts = win._tab_instances["Appointments"]
    appts.panel._widgets["appt_datetime"].insert(0, "2099-01-01 09:00")
    appts.panel._widgets["reason"].insert(0, "Follow-up")
    appts.panel._save()
    root.update()
    assert len(appts.panel._records) == 1

    # Documents (no file attached)
    docs = win._tab_instances["Documents"]
    docs.panel._widgets["title"].insert(0, "Consent Form")
    docs.panel._widgets["doc_type"].set("consent")
    docs.panel._save()
    root.update()
    assert len(docs.panel._records) == 1

    # Billing: invoice
    billing = win._tab_instances["Billing"]
    billing.invoices_panel._widgets["amount_due"].insert(0, "150")
    billing.invoices_panel._save()
    root.update()
    assert len(billing.invoices_panel._records) == 1

    # Timeline should now show multiple aggregated events
    timeline = win._tab_instances["Clinical Timeline"]
    timeline.load_patient()
    root.update()
    assert len(timeline.tree.get_children()) >= 3

    # Reporting: clinic stats + PDF export
    win.reporting_tab._refresh_stats()
    root.update()
    assert "Total patients" in win.reporting_tab.stats_text.get("1.0", "end")


def test_patient_search_and_reselect(root, db, logged_in_user):
    win = MainWindow(root, db, logged_in_user)
    root.update()
    from app.db.dao import patients as patients_dao
    pid = patients_dao.create_patient(db, first_name="Carol", last_name="Danvers", dob="1970-01-01")
    win.search_var.set("Danvers")
    win._refresh_patient_search()
    root.update()
    assert pid in win._patient_list_ids
    win.patient_list.selection_clear(0, "end")
    win.patient_list.selection_set(win._patient_list_ids.index(pid))
    win._on_patient_selected()
    root.update()
    assert win.current_patient_id == pid


def test_dashboard_refresh_no_crash(root, db, logged_in_user):
    win = MainWindow(root, db, logged_in_user)
    root.update()
    win.dashboard_tab.refresh()
    root.update()


def test_admin_tab_create_user(root, db, logged_in_user):
    win = MainWindow(root, db, logged_in_user)
    root.update()
    admin = win.admin_tab
    admin.users_panel._widgets["username"].insert(0, "newclinician")
    admin.users_panel._widgets["full_name"].insert(0, "New Clinician")
    admin.users_panel._widgets["password"].insert(0, "temp12345")
    admin.users_panel._widgets["role"].set("clinician")
    admin.users_panel._save()
    root.update()
    assert any(u["username"] == "newclinician" for u in users_dao.list_users(db))
