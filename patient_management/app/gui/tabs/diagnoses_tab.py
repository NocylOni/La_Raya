"""Module 4: Diagnoses tab (ICD codes, problem list, chronic conditions)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.db.dao import diagnoses as diagnoses_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.logic.icd_codes import search_icd_codes


class DiagnosesTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))
        ttk.Label(toolbar, text="ICD lookup:").pack(side="left")
        self.icd_search_var = tk.StringVar()
        entry = ttk.Entry(toolbar, textvariable=self.icd_search_var, width=25)
        entry.pack(side="left", padx=4)
        entry.bind("<KeyRelease>", self._on_icd_search)
        self.icd_results = ttk.Combobox(toolbar, state="readonly", width=55)
        self.icd_results.pack(side="left", padx=4)
        ttk.Button(toolbar, text="Use Code", command=self._use_icd_code).pack(side="left")

        self.panel = RecordPanel(
            self,
            columns=[("icd_code", "ICD Code"), ("description", "Description"),
                     ("status", "Status"), ("chronic", "Chronic")],
            fields=[
                FieldSpec("icd_code", "ICD Code"),
                FieldSpec("description", "Description"),
                FieldSpec("icd_system", "Code System", kind="combo",
                          options=["ICD-10", "ICD-11"]),
                FieldSpec("status", "Status", kind="combo", options=["active", "resolved"]),
                FieldSpec("chronic", "Chronic Condition", kind="check"),
                FieldSpec("onset_date", "Onset Date"),
                FieldSpec("resolved_date", "Resolved Date"),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_diagnoses,
            on_create=self._create_diagnosis,
            on_update=self._update_diagnosis,
            on_delete=diagnoses_dao.delete_diagnosis,
        )
        self.panel.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    def load_patient(self):
        self.panel.refresh()

    def _on_icd_search(self, _event=None):
        term = self.icd_search_var.get()
        matches = search_icd_codes(term)[:20]
        self.icd_results.configure(values=[f"{c} - {d}" for c, d in matches])

    def _use_icd_code(self):
        value = self.icd_results.get()
        if not value or " - " not in value:
            return
        code, description = value.split(" - ", 1)
        self.panel.apply_values({"icd_code": code, "description": description})

    def _list_diagnoses(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return diagnoses_dao.list_diagnoses(self.ctx.db, pid)

    def _create_diagnosis(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        icd_code = data.pop("icd_code")
        description = data.pop("description")
        diag_id = diagnoses_dao.add_diagnosis(self.ctx.db, pid, icd_code, description, **data)
        self.ctx.audit("ADD_DIAGNOSIS", "diagnosis", diag_id, f"{icd_code} {description}")
        return diag_id

    def _update_diagnosis(self, diagnosis_id, data):
        data = clean_form_values(data)
        data.pop("icd_code", None)
        diagnoses_dao.update_diagnosis(self.ctx.db, diagnosis_id, **data)
        self.ctx.audit("UPDATE_DIAGNOSIS", "diagnosis", diagnosis_id)
