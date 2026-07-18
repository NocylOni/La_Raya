"""Module 7: Treatment Plan tab (therapies, referrals, follow-up, goals)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import plans as plans_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values


class PlansTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.panel = RecordPanel(
            self,
            columns=[("therapy", "Therapy"), ("referral_to", "Referral"),
                     ("follow_up_date", "Follow-up"), ("status", "Status")],
            fields=[
                FieldSpec("therapy", "Therapy / Intervention"),
                FieldSpec("referral_to", "Referral To"),
                FieldSpec("follow_up_date", "Follow-up Date"),
                FieldSpec("instructions", "Patient Instructions", kind="text"),
                FieldSpec("goals", "Goals", kind="text"),
                FieldSpec("status", "Status", kind="combo", options=["open", "completed"]),
            ],
            on_list=self._list_plans,
            on_create=self._create_plan,
            on_update=self._update_plan,
            on_delete=plans_dao.delete_plan,
        )
        self.panel.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

    def load_patient(self):
        self.panel.refresh()

    def _list_plans(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return plans_dao.list_plans(self.ctx.db, pid)

    def _create_plan(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        plan_id = plans_dao.create_plan(self.ctx.db, pid, **data)
        self.ctx.audit("CREATE_PLAN", "treatment_plan", plan_id)
        return plan_id

    def _update_plan(self, plan_id, data):
        data = clean_form_values(data)
        plans_dao.update_plan(self.ctx.db, plan_id, **data)
        self.ctx.audit("UPDATE_PLAN", "treatment_plan", plan_id)
