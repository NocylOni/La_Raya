"""Clinic-wide dashboard: today's appointments, overdue follow-ups, abnormal
labs (QoL: clinical alerts, at-a-glance clinic overview)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import appointments as appointments_dao
from app.i18n import t
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

        ttk.Button(self, text=t("common.refresh"), style="primary.TButton",
                   command=self.refresh).grid(row=0, column=0, sticky="w", padx=6, pady=6)

        appts_frame = ttk.LabelFrame(self, text=t("dashboard.today_appointments"), padding=8)
        appts_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        appts_frame.columnconfigure(0, weight=1)
        appts_frame.rowconfigure(0, weight=1)
        self.appts_tree = ttk.Treeview(
            appts_frame, columns=("time", "patient", "reason", "status"), show="headings"
        )
        for key, header in (("time", t("dashboard.col_time")), ("patient", t("dashboard.col_patient")),
                             ("reason", t("dashboard.col_reason")), ("status", t("dashboard.col_status"))):
            self.appts_tree.heading(key, text=header)
            self.appts_tree.column(key, width=110)
        self.appts_tree.grid(row=0, column=0, sticky="nsew")

        alerts_frame = ttk.LabelFrame(self, text=t("dashboard.clinical_alerts"), padding=8)
        alerts_frame.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
        alerts_frame.columnconfigure(0, weight=1)
        alerts_frame.rowconfigure(0, weight=1)
        self.alerts_tree = ttk.Treeview(
            alerts_frame, columns=("kind", "patient", "detail"), show="headings"
        )
        for key, header in (("kind", t("dashboard.col_alert")), ("patient", t("dashboard.col_patient")),
                             ("detail", t("dashboard.col_detail"))):
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
                values=(t("dashboard.alert_overdue"), f"{item['first_name']} {item['last_name']}",
                        t("dashboard.due_on", date=item["follow_up_date"])),
                tags=("overdue",),
            )
        for item in data["recent_abnormal_results"]:
            self.alerts_tree.insert(
                "", "end",
                values=(t("dashboard.alert_abnormal"), f"{item['first_name']} {item['last_name']}",
                        f"{item['result_name']}: {item['value']} [{item['abnormal_flag']}]"),
                tags=("abnormal",),
            )
        self.alerts_tree.tag_configure("overdue", background="#fdf6e3")
        self.alerts_tree.tag_configure("abnormal", background="#fdeeea")
