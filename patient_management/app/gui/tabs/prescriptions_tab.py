"""Module 6: Prescriptions tab (with interaction/allergy alerts)."""
from __future__ import annotations

from tkinter import messagebox, ttk

from app.db.dao import prescriptions as prescriptions_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.i18n import t
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
            columns=[("medication_name", t("rx.col_medication")), ("dosage", t("rx.col_dosage")),
                     ("frequency", t("rx.col_frequency")), ("status", t("rx.col_status")),
                     ("refills_remaining", t("rx.col_refills_left"))],
            fields=[
                FieldSpec("medication_name", t("rx.medication_name")),
                FieldSpec("dosage", t("rx.dosage")),
                FieldSpec("route", t("rx.route")),
                FieldSpec("frequency", t("rx.frequency")),
                FieldSpec("duration", t("rx.duration")),
                FieldSpec("quantity", t("rx.quantity")),
                FieldSpec("refills", t("rx.refills")),
                FieldSpec("prescriber", t("rx.prescriber")),
                FieldSpec("status", t("rx.status"), kind="combo",
                          options=[t("rx.status.active"), t("rx.status.completed"),
                                   t("rx.status.cancelled")],
                          option_values=["active", "completed", "cancelled"]),
                FieldSpec("start_date", t("rx.start_date")),
                FieldSpec("end_date", t("rx.end_date")),
                FieldSpec("notes", t("rx.notes"), kind="text"),
            ],
            on_list=self._list_prescriptions,
            on_create=self._create_prescription,
            on_update=self._update_prescription,
            on_delete=prescriptions_dao.delete_prescription,
        )
        self.panel.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        ttk.Button(self, text=t("rx.refill_selected"), style="outline.TButton",
                   command=self._refill_selected).grid(
            row=1, column=0, sticky="w", padx=6, pady=(0, 6)
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
                lines.append(t("rx.alert_interaction", severity=item["severity"],
                                drug=item["drug_b"], description=item["description"]))
            for item in check["allergy_conflicts"]:
                lines.append(t("rx.alert_allergy", substance=item["substance"],
                                severity=item["severity"]))
            proceed = messagebox.askyesno(
                t("rx.alert_title"), t("rx.alert_question", lines="\n".join(lines)),
            )
            if not proceed:
                raise ValueError(t("rx.cancelled_by_alert"))

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
            messagebox.showinfo(t("rx.no_refills_title"), t("rx.no_refills_message"))
