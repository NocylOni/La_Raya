"""Module 11: Clinical Timeline tab (chronological view of all patient events)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import timeline as timeline_dao
from app.i18n import t

_EVENT_TYPE_KEYS = {
    "visit": "timeline.type.visit",
    "diagnosis": "timeline.type.diagnosis",
    "prescription": "timeline.type.prescription",
    "order": "timeline.type.order",
    "result": "timeline.type.result",
    "appointment": "timeline.type.appointment",
}


class TimelineTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        columns = ("timestamp", "type", "summary")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for key, header, width in (
            ("timestamp", t("timeline.col_datetime"), 140),
            ("type", t("timeline.col_event"), 130),
            ("summary", t("timeline.col_summary"), 500),
        ):
            self.tree.heading(key, text=header)
            self.tree.column(key, width=width, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("visit", background="#eaf2fb")
        self.tree.tag_configure("diagnosis", background="#fdeeea")
        self.tree.tag_configure("prescription", background="#eafbea")
        self.tree.tag_configure("order", background="#fdf6e3")
        self.tree.tag_configure("result", background="#fdf6e3")
        self.tree.tag_configure("appointment", background="#f2eafb")

    def load_patient(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        pid = self.ctx.current_patient_id
        if pid is None:
            return
        for event in timeline_dao.get_timeline(self.ctx.db, pid):
            event_type = event["type"]
            self.tree.insert(
                "", "end",
                values=(event["timestamp"], t(_EVENT_TYPE_KEYS.get(event_type, event_type)),
                        event["summary"]),
                tags=(event_type,),
            )
