"""Module 12: Reporting & Analytics tab (patient summaries, outcome reports,
clinic statistics, disease registries)."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.db.dao import reporting as reporting_dao
from app.i18n import t
from app.logic import pdf_export


class ReportingTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ttk.Button(toolbar, text=t("reporting.refresh_stats"), style="primary.TButton",
                   command=self._refresh_stats).pack(side="left")
        ttk.Button(toolbar, text=t("reporting.export_patient_pdf"), style="outline.TButton",
                   command=self._export_patient_pdf).pack(side="left", padx=8)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

        self.stats_text = tk.Text(nb, wrap="word", height=20, font=("Helvetica", 10))
        nb.add(self.stats_text, text=t("reporting.tab_stats"))

        registry_frame = ttk.Frame(nb)
        registry_frame.columnconfigure(0, weight=1)
        registry_frame.rowconfigure(1, weight=1)
        search_bar = ttk.Frame(registry_frame)
        search_bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(search_bar, text=t("reporting.diagnosis_contains")).pack(side="left")
        self.registry_term = ttk.Entry(search_bar, width=30)
        self.registry_term.pack(side="left", padx=6)
        ttk.Button(search_bar, text=t("reporting.search_registry"), style="outline.TButton",
                   command=self._search_registry).pack(side="left")
        self.registry_tree = ttk.Treeview(
            registry_frame, columns=("mrn", "name", "dob", "code", "description"), show="headings"
        )
        for key, header in (("mrn", t("reporting.col_mrn")), ("name", t("reporting.col_name")),
                             ("dob", t("reporting.col_dob")), ("code", t("reporting.col_code")),
                             ("description", t("reporting.col_description"))):
            self.registry_tree.heading(key, text=header)
            self.registry_tree.column(key, width=120)
        self.registry_tree.grid(row=1, column=0, sticky="nsew")
        nb.add(registry_frame, text=t("reporting.tab_registry"))

    def load_patient(self):
        pass  # this tab is clinic-wide, not patient-scoped

    def _refresh_stats(self):
        stats = reporting_dao.clinic_statistics(self.ctx.db)
        self.stats_text.delete("1.0", "end")
        lines = [
            t("reporting.stat_total_patients", n=stats["total_patients"]),
            t("reporting.stat_total_visits", n=stats["total_visits"]),
            t("reporting.stat_no_shows", n=stats["no_shows"]),
            t("reporting.stat_cancellations", n=stats["cancellations"]),
            t("reporting.stat_revenue", amount=f"{stats['total_revenue']:.2f}"),
            t("reporting.stat_outstanding", amount=f"{stats['outstanding_balance']:.2f}"),
            "",
            t("reporting.stat_top_diagnoses"),
        ]
        for row in stats["top_diagnoses"]:
            lines.append(f"  {row['icd_code']} - {row['description']}: {row['n']}")
        self.stats_text.insert("1.0", "\n".join(lines))

    def _search_registry(self):
        for row in self.registry_tree.get_children():
            self.registry_tree.delete(row)
        term = self.registry_term.get().strip()
        rows = reporting_dao.disease_registry(self.ctx.db, description_like=term or None)
        for row in rows:
            self.registry_tree.insert(
                "", "end",
                values=(row["mrn"], f"{row['first_name']} {row['last_name']}", row["dob"],
                        row["icd_code"], row["description"]),
            )

    def _export_patient_pdf(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            messagebox.showinfo(t("common.no_patient_title"), t("common.no_patient_message"))
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        pdf_export.export_patient_summary_pdf(self.ctx.db, pid, path)
        self.ctx.audit("EXPORT_PATIENT_PDF", "patient", pid, path)
        messagebox.showinfo(t("common.exported_title"), t("reporting.exported_message", path=path))
