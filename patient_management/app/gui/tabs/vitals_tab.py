"""Vitals recording + trend graphs (part of Module 3, QoL graphs feature)."""
from __future__ import annotations

from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.db.dao import visits as visits_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.i18n import t

NUMERIC_FIELDS = ["height_cm", "weight_kg", "temp_c", "heart_rate", "resp_rate",
                   "bp_systolic", "bp_diastolic", "spo2", "pain_score"]


def _vitals_fields() -> list[FieldSpec]:
    return [
        FieldSpec("recorded_at", t("vitals.recorded_at")),
        FieldSpec("height_cm", t("vitals.height")),
        FieldSpec("weight_kg", t("vitals.weight")),
        FieldSpec("temp_c", t("vitals.temp")),
        FieldSpec("heart_rate", t("vitals.heart_rate")),
        FieldSpec("resp_rate", t("vitals.resp_rate")),
        FieldSpec("bp_systolic", t("vitals.bp_systolic")),
        FieldSpec("bp_diastolic", t("vitals.bp_diastolic")),
        FieldSpec("spo2", t("vitals.spo2")),
        FieldSpec("pain_score", t("vitals.pain_score")),
    ]


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
            columns=[("recorded_at", t("vitals.col_when")), ("bp_systolic", t("vitals.col_bp_sys")),
                     ("bp_diastolic", t("vitals.col_bp_dia")), ("heart_rate", t("vitals.col_hr")),
                     ("bmi", t("vitals.col_bmi"))],
            fields=_vitals_fields(),
            on_list=self._list_vitals,
            on_create=self._create_vitals,
            on_delete=visits_dao.delete_vitals,
            on_change=self._refresh_graph,
        )
        self.panel.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        graph_frame = ttk.LabelFrame(self, text=t("vitals.trend_title"), padding=8)
        graph_frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(1, weight=1)

        ttk.Label(graph_frame, text=t("vitals.metric")).grid(row=0, column=0, sticky="w")
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
                self.ax.plot(range(len(xs)), ys, marker="o", color="#2c3e50")
                self.ax.set_xticks(range(len(xs)))
                self.ax.set_xticklabels([x[:10] for x in xs], rotation=45, ha="right", fontsize=7)
        self.ax.set_title(metric)
        self.figure.tight_layout()
        self.canvas.draw_idle()
