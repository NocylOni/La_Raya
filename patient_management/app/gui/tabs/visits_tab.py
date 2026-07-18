"""Module 3: Visits / Encounters tab (SOAP notes)."""
from __future__ import annotations

from tkinter import ttk

from app.db.dao import templates as templates_dao
from app.db.dao import visits as visits_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.i18n import t


def _soap_fields() -> list[FieldSpec]:
    return [
        FieldSpec("visit_date", t("visits.visit_date")),
        FieldSpec("provider", t("visits.provider")),
        FieldSpec("visit_type", t("visits.visit_type"), kind="combo",
                  options=[t("visit_type.office"), t("visit_type.follow_up"),
                           t("visit_type.telehealth"), t("visit_type.urgent"),
                           t("visit_type.annual")],
                  option_values=["office visit", "follow-up", "telehealth", "urgent",
                                 "annual physical"]),
        FieldSpec("chief_complaint", t("visits.chief_complaint")),
        FieldSpec("hpi", t("visits.hpi"), kind="text"),
        FieldSpec("ros", t("visits.ros"), kind="text"),
        FieldSpec("physical_exam", t("visits.physical_exam"), kind="text"),
        FieldSpec("assessment", t("visits.assessment"), kind="text"),
        FieldSpec("plan", t("visits.plan"), kind="text"),
        FieldSpec("notes", t("visits.notes"), kind="text"),
    ]


class VisitsTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        ttk.Label(toolbar, text=t("visits.apply_template")).pack(side="left")
        self.template_combo = ttk.Combobox(toolbar, state="readonly", width=30)
        self.template_combo.pack(side="left", padx=6)
        ttk.Button(toolbar, text=t("visits.apply"), style="outline.TButton",
                   command=self._apply_template).pack(side="left")
        ttk.Button(toolbar, text=t("visits.export_pdf"), style="outline.TButton",
                   command=self._export_pdf).pack(side="right")

        self.panel = RecordPanel(
            self,
            columns=[("visit_date", t("visits.col_date")), ("visit_type", t("visits.col_type")),
                     ("chief_complaint", t("visits.col_complaint"))],
            fields=_soap_fields(),
            on_list=self._list_visits,
            on_create=self._create_visit,
            on_update=self._update_visit,
            on_delete=visits_dao.delete_visit,
        )
        self.panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

    def load_patient(self):
        self.panel.refresh()
        self._load_templates()

    def _load_templates(self):
        rows = templates_dao.list_templates(self.ctx.db, category="visit_note")
        self._templates = {r["name"]: r["id"] for r in rows}
        self.template_combo.configure(values=list(self._templates.keys()))

    def _apply_template(self):
        name = self.template_combo.get()
        if not name or name not in getattr(self, "_templates", {}):
            return
        template = templates_dao.get_template(self.ctx.db, self._templates[name])
        if template:
            self.panel.apply_values(template["content"])

    def _export_pdf(self):
        from tkinter import filedialog, messagebox

        selection = self.panel.tree.selection()
        if not selection:
            messagebox.showinfo(t("visits.select_visit_title"), t("visits.select_visit_message"))
            return
        visit_id = int(selection[0])
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                             filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        from app.logic import pdf_export
        pdf_export.export_visit_note_pdf(self.ctx.db, visit_id, path)
        self.ctx.audit("EXPORT_VISIT_PDF", "visit", visit_id, path)
        messagebox.showinfo(t("common.exported_title"), path)

    # ------------------------------------------------------------ CRUD glue
    def _list_visits(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return visits_dao.list_visits(self.ctx.db, pid)

    def _create_visit(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        visit_id = visits_dao.create_visit(self.ctx.db, pid, **data)
        self.ctx.audit("CREATE_VISIT", "visit", visit_id)
        return visit_id

    def _update_visit(self, visit_id, data):
        data = clean_form_values(data)
        visits_dao.update_visit(self.ctx.db, visit_id, **data)
        self.ctx.audit("UPDATE_VISIT", "visit", visit_id)
