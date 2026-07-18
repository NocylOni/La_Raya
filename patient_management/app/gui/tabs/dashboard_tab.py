"""Clinic-wide dashboard: today's appointments, overdue follow-ups, abnormal
labs (QoL: clinical alerts, at-a-glance clinic overview)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import appointments as appointments_dao
from app.logic import alerts as alerts_logic


class DashboardTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Button(self, text="Refresh", command=self.refresh).grid(
            row=0, column=0, sticky="w", padx=4, pady=4
        )

        appts_frame = ttk.LabelFrame(self, text="Today's Appointments")
        appts_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        appts_frame.columnconfigure(0, weight=1)
        appts_frame.rowconfigure(0, weight=1)
        self.appts_tree = ttk.Treeview(
            appts_frame, columns=("time", "patient", "reason", "status"), show="headings"
        )
        for key, header in (("time", "Time"), ("patient", "Patient"),
                             ("reason", "Reason"), ("status", "Status")):
            self.appts_tree.heading(key, text=header)
            self.appts_tree.column(key, width=110)
        self.appts_tree.grid(row=0, column=0, sticky="nsew")

        alerts_frame = ttk.LabelFrame(self, text="Clinical Alerts")
        alerts_frame.grid(row=1, column=1, sticky="nsew", padx=4, pady=4)
        alerts_frame.columnconfigure(0, weight=1)
        alerts_frame.rowconfigure(0, weight=1)
        self.alerts_tree = ttk.Treeview(
            alerts_frame, columns=("kind", "patient", "detail"), show="headings"
        )
        for key, header in (("kind", "Alert"), ("patient", "Patient"), ("detail", "Detail")):
            self.alerts_tree.heading(key, text=header)
            self.alerts_tree.column(key, width=150)
        self.alerts_tree.grid(row=0, column=0, sticky="nsew")

    def refresh(self):
        for row in self.appts_tree.get_children():
            self.appts_tree.delete(row)
        for row in appointments_dao.todays_appointments(self.ctx.db):
            self.appts_tree.insert(
                "", "end",
                values=(row["appt_datetime"], f"{row['first_name']} {row['last_name']}",
                        row["reason"] or "", row["status"]),
            )

        for row in self.alerts_tree.get_children():
            self.alerts_tree.delete(row)
        data = alerts_logic.clinic_wide_alerts(self.ctx.db)
        for item in data["overdue_follow_ups"]:
            self.alerts_tree.insert(
                "", "end",
                values=("Overdue follow-up", f"{item['first_name']} {item['last_name']}",
                        f"Due {item['follow_up_date']}"),
                tags=("overdue",),
            )
        for item in data["recent_abnormal_results"]:
            self.alerts_tree.insert(
                "", "end",
                values=("Abnormal result", f"{item['first_name']} {item['last_name']}",
                        f"{item['result_name']}: {item['value']} [{item['abnormal_flag']}]"),
                tags=("abnormal",),
            )
        self.alerts_tree.tag_configure("overdue", background="#fdf6e3")
        self.alerts_tree.tag_configure("abnormal", background="#fdeeea")
