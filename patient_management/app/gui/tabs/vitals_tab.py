"""Vitals recording + trend graphs (part of Module 3, QoL graphs feature)."""
from __future__ import annotations

from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.db.dao import visits as visits_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values

VITALS_FIELDS = [
    FieldSpec("recorded_at", "Recorded At (YYYY-MM-DD HH:MM)"),
    FieldSpec("height_cm", "Height (cm)"),
    FieldSpec("weight_kg", "Weight (kg)"),
    FieldSpec("temp_c", "Temp (C)"),
    FieldSpec("heart_rate", "Heart Rate"),
    FieldSpec("resp_rate", "Resp. Rate"),
    FieldSpec("bp_systolic", "BP Systolic"),
    FieldSpec("bp_diastolic", "BP Diastolic"),
    FieldSpec("spo2", "SpO2 (%)"),
    FieldSpec("pain_score", "Pain Score (0-10)"),
]

NUMERIC_FIELDS = ["height_cm", "weight_kg", "temp_c", "heart_rate", "resp_rate",
                   "bp_systolic", "bp_diastolic", "spo2", "pain_score"]


class VitalsTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.panel = RecordPanel(
            self,
            columns=[("recorded_at", "When"), ("bp_systolic", "BP Sys"),
                     ("bp_diastolic", "BP Dia"), ("heart_rate", "HR"), ("bmi", "BMI")],
            fields=VITALS_FIELDS,
            on_list=self._list_vitals,
            on_create=self._create_vitals,
            on_delete=visits_dao.delete_vitals,
            on_change=self._refresh_graph,
        )
        self.panel.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        graph_frame = ttk.LabelFrame(self, text="Vitals Trend")
        graph_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(1, weight=1)

        ttk.Label(graph_frame, text="Metric:").grid(row=0, column=0, sticky="w")
        self.metric_combo = ttk.Combobox(
            graph_frame, state="readonly",
            values=["heart_rate", "bp_systolic", "bp_diastolic", "weight_kg", "bmi", "spo2"],
        )
        self.metric_combo.set("heart_rate")
        self.metric_combo.grid(row=0, column=0, sticky="e")
        self.metric_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_graph())

        self.figure = Figure(figsize=(4.5, 3.5), dpi=90)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    def load_patient(self):
        self.panel.refresh()
        self._refresh_graph()

    def _list_vitals(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return visits_dao.list_vitals(self.ctx.db, pid)

    def _create_vitals(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data, numeric_fields=NUMERIC_FIELDS)
        vitals_id = visits_dao.record_vitals(self.ctx.db, pid, **data)
        self.ctx.audit("RECORD_VITALS", "vitals", vitals_id)
        return vitals_id

    def _refresh_graph(self):
        self.ax.clear()
        pid = self.ctx.current_patient_id
        metric = self.metric_combo.get() or "heart_rate"
        if pid is not None:
            rows = visits_dao.list_vitals(self.ctx.db, pid)
            xs = [r["recorded_at"] for r in rows if r[metric] is not None]
            ys = [r[metric] for r in rows if r[metric] is not None]
            if xs:
                self.ax.plot(range(len(xs)), ys, marker="o")
                self.ax.set_xticks(range(len(xs)))
                self.ax.set_xticklabels([x[:10] for x in xs], rotation=45, ha="right", fontsize=7)
        self.ax.set_title(metric)
        self.figure.tight_layout()
        self.canvas.draw_idle()
