"""Module 6: Prescriptions tab (with interaction/allergy alerts)."""
from __future__ import annotations

from tkinter import messagebox, ttk

from app.db.dao import prescriptions as prescriptions_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.logic import alerts as alerts_logic


class PrescriptionsTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.panel = RecordPanel(
            self,
            columns=[("medication_name", "Medication"), ("dosage", "Dosage"),
                     ("frequency", "Frequency"), ("status", "Status"),
                     ("refills_remaining", "Refills Left")],
            fields=[
                FieldSpec("medication_name", "Medication Name"),
                FieldSpec("dosage", "Dosage"),
                FieldSpec("route", "Route"),
                FieldSpec("frequency", "Frequency"),
                FieldSpec("duration", "Duration"),
                FieldSpec("quantity", "Quantity"),
                FieldSpec("refills", "Refills Authorized"),
                FieldSpec("prescriber", "Prescriber"),
                FieldSpec("status", "Status", kind="combo",
                          options=["active", "completed", "cancelled"]),
                FieldSpec("start_date", "Start Date"),
                FieldSpec("end_date", "End Date"),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_prescriptions,
            on_create=self._create_prescription,
            on_update=self._update_prescription,
            on_delete=prescriptions_dao.delete_prescription,
        )
        self.panel.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        ttk.Button(self, text="Refill Selected", command=self._refill_selected).grid(
            row=1, column=0, sticky="w", padx=4, pady=(0, 4)
        )

    def load_patient(self):
        self.panel.refresh()

    def _list_prescriptions(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return prescriptions_dao.list_prescriptions(self.ctx.db, pid)

    def _create_prescription(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data, numeric_fields=["quantity", "refills"])
        medication_name = data.pop("medication_name")

        check = alerts_logic.check_new_prescription(self.ctx.db, pid, medication_name)
        if check["has_alerts"]:
            lines = []
            for item in check["interactions"]:
                lines.append(f"Interaction ({item['severity']}) with {item['drug_b']}: "
                             f"{item['description']}")
            for item in check["allergy_conflicts"]:
                lines.append(f"Allergy conflict: patient is allergic to {item['substance']} "
                             f"({item['severity']})")
            proceed = messagebox.askyesno(
                "Clinical Alert",
                "The following alerts were found:\n\n" + "\n".join(lines) +
                "\n\nPrescribe anyway?",
            )
            if not proceed:
                raise ValueError("Prescription cancelled due to clinical alert")

        rx_id = prescriptions_dao.create_prescription(self.ctx.db, pid, medication_name, **data)
        self.ctx.audit("CREATE_PRESCRIPTION", "prescription", rx_id, medication_name)
        return rx_id

    def _update_prescription(self, rx_id, data):
        data = clean_form_values(data, numeric_fields=["quantity", "refills", "refills_remaining"])
        data.pop("medication_name", None)
        prescriptions_dao.update_prescription(self.ctx.db, rx_id, **data)
        self.ctx.audit("UPDATE_PRESCRIPTION", "prescription", rx_id)

    def _refill_selected(self):
        selection = self.panel.tree.selection()
        if not selection:
            return
        rx_id = int(selection[0])
        ok = prescriptions_dao.refill_prescription(self.ctx.db, rx_id)
        if ok:
            self.ctx.audit("REFILL_PRESCRIPTION", "prescription", rx_id)
            self.panel.refresh()
        else:
            messagebox.showinfo("No refills", "No refills remaining for this prescription.")
