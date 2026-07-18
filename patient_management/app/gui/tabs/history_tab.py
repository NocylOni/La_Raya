"""Module 2: Medical History tab (past medical/surgical, family, social,
medications, immunizations)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import history as history_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values

CATEGORY_LABELS = {
    "past_medical": "Past Medical History",
    "past_surgical": "Past Surgical History",
    "family": "Family History",
    "social": "Social History",
}


class HistoryTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.panels: list[RecordPanel] = []
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sub_nb = ttk.Notebook(self)
        sub_nb.grid(row=0, column=0, sticky="nsew")

        for category, label in CATEGORY_LABELS.items():
            panel = RecordPanel(
                sub_nb,
                columns=[("description", "Description"), ("onset_date", "Onset"),
                         ("status", "Status")],
                fields=[
                    FieldSpec("description", "Description", kind="text"),
                    FieldSpec("onset_date", "Onset Date"),
                    FieldSpec("resolved_date", "Resolved Date"),
                    FieldSpec("status", "Status", kind="combo", options=["active", "resolved"]),
                    FieldSpec("notes", "Notes", kind="text"),
                ],
                on_list=self._make_list_fn(category),
                on_create=self._make_create_fn(category),
                on_delete=history_dao.delete_history_item,
            )
            sub_nb.add(panel, text=label)
            self.panels.append(panel)

        self.immunization_panel = RecordPanel(
            sub_nb,
            columns=[("vaccine", "Vaccine"), ("date_given", "Date Given"), ("dose", "Dose")],
            fields=[
                FieldSpec("vaccine", "Vaccine"), FieldSpec("date_given", "Date Given"),
                FieldSpec("dose", "Dose"), FieldSpec("lot_number", "Lot #"),
                FieldSpec("site", "Site"), FieldSpec("provider", "Provider"),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_immunizations,
            on_create=self._create_immunization,
            on_delete=history_dao.delete_immunization,
        )
        sub_nb.add(self.immunization_panel, text="Immunizations")
        self.panels.append(self.immunization_panel)

        self.medication_panel = RecordPanel(
            sub_nb,
            columns=[("name", "Medication"), ("dosage", "Dosage"), ("status", "Status")],
            fields=[
                FieldSpec("name", "Medication Name"), FieldSpec("dosage", "Dosage"),
                FieldSpec("route", "Route"), FieldSpec("frequency", "Frequency"),
                FieldSpec("start_date", "Start Date"), FieldSpec("end_date", "End Date"),
                FieldSpec("status", "Status", kind="combo",
                          options=["active", "discontinued", "completed"]),
                FieldSpec("prescribing_provider", "Prescriber"),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_medication_history,
            on_create=self._create_medication_history,
            on_delete=history_dao.delete_medication_history,
        )
        sub_nb.add(self.medication_panel, text="Medication History")
        self.panels.append(self.medication_panel)

    def load_patient(self):
        for panel in self.panels:
            panel.refresh()

    # ------------------------------------------------------------ helpers
    def _make_list_fn(self, category):
        def _list():
            pid = self.ctx.current_patient_id
            if pid is None:
                return []
            return history_dao.list_history(self.ctx.db, pid, category=category)
        return _list

    def _make_create_fn(self, category):
        def _create(data):
            pid = self.ctx.require_patient()
            data = clean_form_values(data)
            description = data.pop("description")
            return history_dao.add_history_item(self.ctx.db, pid, category, description, **data)
        return _create

    def _list_immunizations(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return history_dao.list_immunizations(self.ctx.db, pid)

    def _create_immunization(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        vaccine = data.pop("vaccine")
        return history_dao.add_immunization(self.ctx.db, pid, vaccine, **data)

    def _list_medication_history(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return history_dao.list_medication_history(self.ctx.db, pid)

    def _create_medication_history(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        name = data.pop("name")
        return history_dao.add_medication_history(self.ctx.db, pid, name, **data)
