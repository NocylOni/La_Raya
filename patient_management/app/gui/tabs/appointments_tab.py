"""Module 8: Appointments tab (scheduling, reminders, cancellations, no-shows)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import appointments as appointments_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values


class AppointmentsTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.panel = RecordPanel(
            self,
            columns=[("appt_datetime", "Date/Time"), ("provider", "Provider"),
                     ("reason", "Reason"), ("status", "Status")],
            fields=[
                FieldSpec("appt_datetime", "Date/Time (YYYY-MM-DD HH:MM)"),
                FieldSpec("provider", "Provider"),
                FieldSpec("duration_minutes", "Duration (min)"),
                FieldSpec("reason", "Reason"),
                FieldSpec("status", "Status", kind="combo",
                          options=["scheduled", "completed", "cancelled", "no-show"]),
                FieldSpec("notes", "Notes", kind="text"),
            ],
            on_list=self._list_appointments,
            on_create=self._create_appointment,
            on_update=self._update_appointment,
            on_delete=appointments_dao.delete_appointment,
        )
        self.panel.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

    def load_patient(self):
        self.panel.refresh()

    def _list_appointments(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return appointments_dao.list_appointments(self.ctx.db, pid)

    def _create_appointment(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data, numeric_fields=["duration_minutes"])
        appt_datetime = data.pop("appt_datetime")
        appt_id = appointments_dao.schedule_appointment(self.ctx.db, pid, appt_datetime, **data)
        self.ctx.audit("SCHEDULE_APPOINTMENT", "appointment", appt_id)
        return appt_id

    def _update_appointment(self, appt_id, data):
        data = clean_form_values(data, numeric_fields=["duration_minutes"])
        new_datetime = data.pop("appt_datetime", None)
        if new_datetime:
            appointments_dao.reschedule_appointment(self.ctx.db, appt_id, new_datetime)
        status = data.pop("status", None)
        if status:
            appointments_dao.update_status(self.ctx.db, appt_id, status)
        self.ctx.audit("UPDATE_APPOINTMENT", "appointment", appt_id)
