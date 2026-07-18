"""Module 1: Patient Registry tab."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.db.dao import patients as patients_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values

DEMOGRAPHIC_FIELDS = [
    ("first_name", "First Name"), ("last_name", "Last Name"), ("dob", "DOB (YYYY-MM-DD)"),
    ("sex", "Sex"), ("gender", "Gender"), ("phone", "Phone"), ("email", "Email"),
    ("address", "Address"), ("city", "City"), ("state", "State"), ("zip_code", "ZIP"),
    ("insurance_provider", "Insurance Provider"), ("insurance_policy_number", "Policy #"),
    ("insurance_group_number", "Group #"), ("pcp_name", "Primary Care Physician"),
    ("pcp_contact", "PCP Contact"), ("status", "Status"),
]


class RegistryTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._entries: dict[str, tk.Entry] = {}
        self._build()

    def _build(self):
        self.columnconfigure(1, weight=1)
        demo_frame = ttk.LabelFrame(self, text="Demographics, Contact & Insurance")
        demo_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        demo_frame.columnconfigure(1, weight=1)
        demo_frame.columnconfigure(3, weight=1)

        for i, (key, label) in enumerate(DEMOGRAPHIC_FIELDS):
            row, col = divmod(i, 2)
            ttk.Label(demo_frame, text=label + ":").grid(
                row=row, column=col * 2, sticky="e", padx=4, pady=2
            )
            entry = ttk.Entry(demo_frame, width=28)
            entry.grid(row=row, column=col * 2 + 1, sticky="ew", padx=4, pady=2)
            self._entries[key] = entry

        ttk.Button(demo_frame, text="Save Demographics", command=self._save_demographics).grid(
            row=len(DEMOGRAPHIC_FIELDS) // 2 + 1, column=0, columnspan=4, pady=6
        )

        sub_nb = ttk.Notebook(self)
        sub_nb.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
        self.rowconfigure(1, weight=1)

        self.contacts_panel = RecordPanel(
            sub_nb,
            columns=[("name", "Name"), ("relationship", "Relationship"), ("phone", "Phone")],
            fields=[
                FieldSpec("name", "Name"), FieldSpec("relationship", "Relationship"),
                FieldSpec("phone", "Phone"), FieldSpec("email", "Email"),
                FieldSpec("address", "Address", kind="text"),
            ],
            on_list=self._list_contacts,
            on_create=self._create_contact,
            on_delete=self._delete_contact,
        )
        sub_nb.add(self.contacts_panel, text="Emergency Contacts")

        self.allergy_panel = RecordPanel(
            sub_nb,
            columns=[("substance", "Substance"), ("reaction", "Reaction"),
                     ("severity", "Severity"), ("status", "Status")],
            fields=[
                FieldSpec("substance", "Substance"), FieldSpec("reaction", "Reaction"),
                FieldSpec("severity", "Severity", kind="combo",
                          options=["mild", "moderate", "severe"]),
                FieldSpec("allergy_type", "Type", kind="combo",
                          options=["drug", "food", "environmental"]),
                FieldSpec("status", "Status", kind="combo", options=["active", "resolved"]),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_allergies,
            on_create=self._create_allergy,
            on_delete=self._delete_allergy,
        )
        sub_nb.add(self.allergy_panel, text="Allergies")

    # ---------------------------------------------------------- demographics
    def load_patient(self):
        patient_id = self.ctx.current_patient_id
        for key, entry in self._entries.items():
            entry.delete(0, "end")
        if patient_id is None:
            return
        row = patients_dao.get_patient(self.ctx.db, patient_id)
        if row is None:
            return
        for key, entry in self._entries.items():
            value = row[key]
            if value is not None:
                entry.insert(0, str(value))
        self.contacts_panel.refresh()
        self.allergy_panel.refresh()

    def _save_demographics(self):
        data = {key: entry.get().strip() for key, entry in self._entries.items()}
        data = clean_form_values(data)
        if not data.get("first_name") or not data.get("last_name") or not data.get("dob"):
            messagebox.showerror("Missing data", "First name, last name and DOB are required.")
            return
        patient_id = self.ctx.current_patient_id
        try:
            if patient_id is None:
                patient_id = patients_dao.create_patient(self.ctx.db, **data)
                self.ctx.set_current_patient(patient_id)
            else:
                patients_dao.update_patient(self.ctx.db, patient_id, **data)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Could not save patient", str(exc))
            return
        self.ctx.audit("SAVE_PATIENT", "patient", patient_id)
        self.ctx.on_patient_saved()
        messagebox.showinfo("Saved", "Patient demographics saved.")

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
