"""Module 12: Reporting & Analytics tab (patient summaries, outcome reports,
clinic statistics, disease registries)."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.db.dao import reporting as reporting_dao
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
        toolbar.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(toolbar, text="Refresh Clinic Statistics", command=self._refresh_stats).pack(
            side="left"
        )
        ttk.Button(toolbar, text="Export Current Patient Summary PDF",
                   command=self._export_patient_pdf).pack(side="left", padx=6)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        self.stats_text = tk.Text(nb, wrap="word", height=20)
        nb.add(self.stats_text, text="Clinic Statistics")

        registry_frame = ttk.Frame(nb)
        registry_frame.columnconfigure(0, weight=1)
        registry_frame.rowconfigure(1, weight=1)
        search_bar = ttk.Frame(registry_frame)
        search_bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(search_bar, text="Diagnosis contains:").pack(side="left")
        self.registry_term = ttk.Entry(search_bar, width=30)
        self.registry_term.pack(side="left", padx=4)
        ttk.Button(search_bar, text="Search Registry", command=self._search_registry).pack(
            side="left"
        )
        self.registry_tree = ttk.Treeview(
            registry_frame, columns=("mrn", "name", "dob", "code", "description"), show="headings"
        )
        for key, header in (("mrn", "MRN"), ("name", "Name"), ("dob", "DOB"),
                             ("code", "ICD Code"), ("description", "Description")):
            self.registry_tree.heading(key, text=header)
            self.registry_tree.column(key, width=120)
        self.registry_tree.grid(row=1, column=0, sticky="nsew")
        nb.add(registry_frame, text="Disease Registry")

    def load_patient(self):
        pass  # this tab is clinic-wide, not patient-scoped

    def _refresh_stats(self):
        stats = reporting_dao.clinic_statistics(self.ctx.db)
        self.stats_text.delete("1.0", "end")
        lines = [
            f"Total patients: {stats['total_patients']}",
            f"Total visits: {stats['total_visits']}",
            f"No-shows: {stats['no_shows']}",
            f"Cancellations: {stats['cancellations']}",
            f"Total revenue collected: ${stats['total_revenue']:.2f}",
            f"Outstanding balance: ${stats['outstanding_balance']:.2f}",
            "",
            "Top diagnoses:",
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
            messagebox.showinfo("No patient selected", "Select a patient first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        pdf_export.export_patient_summary_pdf(self.ctx.db, pid, path)
        self.ctx.audit("EXPORT_PATIENT_PDF", "patient", pid, path)
        messagebox.showinfo("Exported", f"Patient summary exported to {path}")
