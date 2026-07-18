"""Module 1: Patient Registry tab."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.db.dao import patients as patients_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.i18n import t

DEMOGRAPHIC_FIELDS = [
    ("first_name", "registry.first_name"), ("last_name", "registry.last_name"),
    ("dob", "registry.dob"), ("sex", "registry.sex"), ("gender", "registry.gender"),
    ("phone", "registry.phone"), ("email", "registry.email"),
    ("address", "registry.address"), ("city", "registry.city"), ("state", "registry.state"),
    ("zip_code", "registry.zip_code"), ("insurance_provider", "registry.insurance_provider"),
    ("insurance_policy_number", "registry.insurance_policy_number"),
    ("insurance_group_number", "registry.insurance_group_number"),
    ("pcp_name", "registry.pcp_name"), ("pcp_contact", "registry.pcp_contact"),
    ("status", "registry.status"),
]


class RegistryTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._entries: dict[str, tk.Entry] = {}
        self._build()

    def _build(self):
        self._status_options = [t("status.active"), t("status.inactive")]
        self._status_values = ["active", "inactive"]

        self.columnconfigure(1, weight=1)
        demo_frame = ttk.LabelFrame(self, text=t("registry.section_demographics"), padding=10)
        demo_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        demo_frame.columnconfigure(1, weight=1)
        demo_frame.columnconfigure(3, weight=1)

        for i, (key, label_key) in enumerate(DEMOGRAPHIC_FIELDS):
            row, col = divmod(i, 2)
            ttk.Label(demo_frame, text=t(label_key) + ":").grid(
                row=row, column=col * 2, sticky="e", padx=6, pady=4
            )
            if key == "status":
                widget = ttk.Combobox(demo_frame, values=self._status_options, width=26,
                                       state="readonly")
            else:
                widget = ttk.Entry(demo_frame, width=28)
            widget.grid(row=row, column=col * 2 + 1, sticky="ew", padx=6, pady=4)
            self._entries[key] = widget

        ttk.Button(demo_frame, text=t("registry.save_demographics"), style="primary.TButton",
                   command=self._save_demographics).grid(
            row=len(DEMOGRAPHIC_FIELDS) // 2 + 1, column=0, columnspan=4, pady=10
        )

        sub_nb = ttk.Notebook(self)
        sub_nb.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        self.rowconfigure(1, weight=1)

        self.contacts_panel = RecordPanel(
            sub_nb,
            columns=[("name", t("registry.col_name")), ("relationship", t("registry.col_relationship")),
                     ("phone", t("registry.col_phone"))],
            fields=[
                FieldSpec("name", t("registry.contact_name")),
                FieldSpec("relationship", t("registry.contact_relationship")),
                FieldSpec("phone", t("registry.contact_phone")),
                FieldSpec("email", t("registry.contact_email")),
                FieldSpec("address", t("registry.contact_address"), kind="text"),
            ],
            on_list=self._list_contacts,
            on_create=self._create_contact,
            on_delete=self._delete_contact,
        )
        sub_nb.add(self.contacts_panel, text=t("registry.tab_contacts"))

        self.allergy_panel = RecordPanel(
            sub_nb,
            columns=[("substance", t("registry.col_substance")), ("reaction", t("registry.col_reaction")),
                     ("severity", t("registry.col_severity")), ("status", t("registry.col_status"))],
            fields=[
                FieldSpec("substance", t("registry.allergy_substance")),
                FieldSpec("reaction", t("registry.allergy_reaction")),
                FieldSpec("severity", t("registry.allergy_severity"), kind="combo",
                          options=[t("severity.mild"), t("severity.moderate"), t("severity.severe")],
                          option_values=["mild", "moderate", "severe"]),
                FieldSpec("allergy_type", t("registry.allergy_type"), kind="combo",
                          options=[t("allergy_type.drug"), t("allergy_type.food"),
                                   t("allergy_type.environmental")],
                          option_values=["drug", "food", "environmental"]),
                FieldSpec("status", t("registry.allergy_status"), kind="combo",
                          options=[t("status.active"), t("status.resolved")],
                          option_values=["active", "resolved"]),
                FieldSpec("notes", t("registry.allergy_notes"), kind="text"),
            ],
            on_list=self._list_allergies,
            on_create=self._create_allergy,
            on_delete=self._delete_allergy,
        )
        sub_nb.add(self.allergy_panel, text=t("registry.tab_allergies"))

    # ---------------------------------------------------------- demographics
    def load_patient(self):
        patient_id = self.ctx.current_patient_id
        for key, entry in self._entries.items():
            if key == "status":
                entry.set("")
            else:
                entry.delete(0, "end")
        if patient_id is None:
            return
        row = patients_dao.get_patient(self.ctx.db, patient_id)
        if row is None:
            return
        for key, entry in self._entries.items():
            value = row[key]
            if value is None:
                continue
            if key == "status":
                if value in self._status_values:
                    entry.set(self._status_options[self._status_values.index(value)])
            else:
                entry.insert(0, str(value))
        self.contacts_panel.refresh()
        self.allergy_panel.refresh()

    def _save_demographics(self):
        data = {}
        for key, entry in self._entries.items():
            if key == "status":
                display = entry.get()
                data[key] = (self._status_values[self._status_options.index(display)]
                              if display in self._status_options else "")
            else:
                data[key] = entry.get().strip()
        data = clean_form_values(data)
        if not data.get("first_name") or not data.get("last_name") or not data.get("dob"):
            messagebox.showerror(t("registry.missing_data_title"), t("registry.missing_data_message"))
            return
        patient_id = self.ctx.current_patient_id
        try:
            if patient_id is None:
                patient_id = patients_dao.create_patient(self.ctx.db, **data)
                self.ctx.set_current_patient(patient_id)
            else:
                patients_dao.update_patient(self.ctx.db, patient_id, **data)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(t("common.error_save_title"), str(exc))
            return
        self.ctx.audit("SAVE_PATIENT", "patient", patient_id)
        self.ctx.on_patient_saved()
        messagebox.showinfo(t("common.saved_title"), t("registry.saved_message"))

    # ---------------------------------------------------------- contacts
    def _list_contacts(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return patients_dao.list_emergency_contacts(self.ctx.db, pid)

    def _create_contact(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        return patients_dao.add_emergency_contact(self.ctx.db, pid, data.pop("name"), **data)

    def _delete_contact(self, contact_id):
        patients_dao.delete_emergency_contact(self.ctx.db, contact_id)

    # ---------------------------------------------------------- allergies
    def _list_allergies(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return patients_dao.list_allergies(self.ctx.db, pid)

    def _create_allergy(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        substance = data.pop("substance")
        allergy_id = patients_dao.add_allergy(self.ctx.db, pid, substance, **data)
        self.ctx.audit("ADD_ALLERGY", "allergy", allergy_id, substance)
        return allergy_id

    def _delete_allergy(self, allergy_id):
        patients_dao.delete_allergy(self.ctx.db, allergy_id)
