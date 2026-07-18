"""Module 9: Documents tab (referrals, discharge summaries, consent forms,
scanned records, PDFs, images)."""
from __future__ import annotations

import os
import platform
import subprocess
from tkinter import filedialog, messagebox, ttk

from app.db.dao import documents as documents_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values
from app.i18n import t

_DOC_TYPE_KEYS = {
    "referral": "doc_type.referral",
    "discharge_summary": "doc_type.discharge_summary",
    "consent": "doc_type.consent",
    "scan": "doc_type.scan",
    "image": "doc_type.image",
    "lab_report": "doc_type.lab_report",
    "other": "doc_type.other",
}


class DocumentsTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._pending_file_path: str | None = None
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        doc_type_labels = [t(key) for key in _DOC_TYPE_KEYS.values()]
        doc_type_values = list(_DOC_TYPE_KEYS.keys())

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        ttk.Button(toolbar, text=t("docs.choose_file"), style="outline.TButton",
                   command=self._choose_file).pack(side="left")
        self.file_label = ttk.Label(toolbar, text=t("docs.no_file_selected"))
        self.file_label.pack(side="left", padx=8)
        ttk.Button(toolbar, text=t("docs.open_selected"), style="outline.TButton",
                   command=self._open_selected).pack(side="right")

        self.panel = RecordPanel(
            self,
            columns=[("title", t("docs.col_title")), ("doc_type", t("docs.col_type")),
                     ("uploaded_at", t("docs.col_uploaded"))],
            fields=[
                FieldSpec("title", t("docs.title")),
                FieldSpec("doc_type", t("docs.type"), kind="combo",
                          options=doc_type_labels, option_values=doc_type_values),
                FieldSpec("uploaded_by", t("docs.uploaded_by")),
                FieldSpec("notes", t("docs.notes"), kind="text"),
            ],
            on_list=self._list_documents,
            on_create=self._create_document,
            on_delete=self._delete_document,
        )
        self.panel.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

    def load_patient(self):
        self.panel.refresh()
        self._pending_file_path = None
        self.file_label.configure(text=t("docs.no_file_selected"))

    def _choose_file(self):
        path = filedialog.askopenfilename()
        if path:
            self._pending_file_path = path
            self.file_label.configure(text=os.path.basename(path))

    def _list_documents(self):
        pid = self.ctx.current_patient_id
        if pid is None:
            return []
        return documents_dao.list_documents(self.ctx.db, pid)

    def _create_document(self, data):
        pid = self.ctx.require_patient()
        data = clean_form_values(data)
        title = data.pop("title")
        stored_path = None
        if self._pending_file_path:
            stored_path = documents_dao.store_file(self._pending_file_path)
        doc_id = documents_dao.add_document(
            self.ctx.db, pid, title, file_path=stored_path, **data
        )
        self.ctx.audit("ADD_DOCUMENT", "document", doc_id, title)
        self._pending_file_path = None
        self.file_label.configure(text=t("docs.no_file_selected"))
        return doc_id

    def _delete_document(self, doc_id):
        documents_dao.delete_document(self.ctx.db, doc_id, remove_file=False)

    def _open_selected(self):
        selection = self.panel.tree.selection()
        if not selection:
            return
        doc = documents_dao.get_document(self.ctx.db, int(selection[0]))
        if doc is None or not doc["file_path"]:
            messagebox.showinfo(t("docs.no_file_title"), t("docs.no_file_message"))
            return
        path = doc["file_path"]
        if not os.path.exists(path):
            messagebox.showerror(t("docs.missing_file_title"), t("docs.missing_file_message", path=path))
            return
        try:
            if platform.system() == "Windows":
                os.startfile(path)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(t("docs.open_error_title"), str(exc))
