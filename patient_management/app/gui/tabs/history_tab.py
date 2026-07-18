"""Module 2: Medical History tab (past medical/surgical, family, social,
medications, immunizations)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import history as history_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.i18n import t

CATEGORY_LABEL_KEYS = {
    "past_medical": "history.past_medical",
    "past_surgical": "history.past_surgical",
    "family": "history.family",
    "social": "history.social",
}

class HistoryTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.panels: list[RecordPanel] = []
        self._build()

    def _build(self):
        status_options = [t("status.active"), t("status.resolved")]
        status_values = ["active", "resolved"]

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sub_nb = ttk.Notebook(self)
        sub_nb.grid(row=0, column=0, sticky="nsew")

        for category, label_key in CATEGORY_LABEL_KEYS.items():
            panel = RecordPanel(
                sub_nb,
                columns=[("description", t("history.col_description")),
                         ("onset_date", t("history.col_onset")),
                         ("status", t("history.col_status"))],
                fields=[
                    FieldSpec("description", t("history.description"), kind="text"),
                    FieldSpec("onset_date", t("history.onset_date")),
                    FieldSpec("resolved_date", t("history.resolved_date")),
                    FieldSpec("status", t("history.status"), kind="combo",
                              options=status_options, option_values=status_values),
                    FieldSpec("notes", t("history.notes"), kind="text"),
                ],
                on_list=self._make_list_fn(category),
                on_create=self._make_create_fn(category),
                on_delete=history_dao.delete_history_item,
            )
            sub_nb.add(panel, text=t(label_key))
            self.panels.append(panel)

        self.immunization_panel = RecordPanel(
            sub_nb,
            columns=[("vaccine", t("history.col_vaccine")), ("date_given", t("history.col_date_given")),
                     ("dose", t("history.col_dose"))],
            fields=[
                FieldSpec("vaccine", t("history.vaccine")),
                FieldSpec("date_given", t("history.date_given")),
                FieldSpec("dose", t("history.dose")),
                FieldSpec("lot_number", t("history.lot_number")),
                FieldSpec("site", t("history.site")),
                FieldSpec("provider", t("history.provider")),
                FieldSpec("notes", t("history.notes"), kind="text"),
            ],
            on_list=self._list_immunizations,
            on_create=self._create_immunization,
            on_delete=history_dao.delete_immunization,
        )
        sub_nb.add(self.immunization_panel, text=t("history.tab_immunizations"))
        self.panels.append(self.immunization_panel)

        self.medication_panel = RecordPanel(
            sub_nb,
            columns=[("name", t("history.col_medication")), ("dosage", t("history.col_dosage")),
                     ("status", t("history.med_status"))],
            fields=[
                FieldSpec("name", t("history.med_name")),
                FieldSpec("dosage", t("history.med_dosage")),
                FieldSpec("route", t("history.med_route")),
                FieldSpec("frequency", t("history.med_frequency")),
                FieldSpec("start_date", t("history.med_start_date")),
                FieldSpec("end_date", t("history.med_end_date")),
                FieldSpec("status", t("history.med_status"), kind="combo",
                          options=[t("med_status.active"), t("med_status.discontinued"),
                                   t("med_status.completed")],
                          option_values=["active", "discontinued", "completed"]),
                FieldSpec("prescribing_provider", t("history.med_prescriber")),
                FieldSpec("notes", t("history.notes"), kind="text"),
            ],
            on_list=self._list_medication_history,
            on_create=self._create_medication_history,
            on_delete=history_dao.delete_medication_history,
        )
        sub_nb.add(self.medication_panel, text=t("history.tab_medications"))
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
