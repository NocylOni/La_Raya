"""Main application window: patient search sidebar + module tabs."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.db.dao import audit as audit_dao
from app.db.dao import patients as patients_dao
from app.db.dao import search as search_dao
from app.db.database import Database
from app.i18n import t

from app.gui.tabs.admin_tab import AdminTab
from app.gui.tabs.appointments_tab import AppointmentsTab
from app.gui.tabs.billing_tab import BillingTab
from app.gui.tabs.dashboard_tab import DashboardTab
from app.gui.tabs.diagnoses_tab import DiagnosesTab
from app.gui.tabs.documents_tab import DocumentsTab
from app.gui.tabs.history_tab import HistoryTab
from app.gui.tabs.orders_tab import OrdersTab
from app.gui.tabs.plans_tab import PlansTab
from app.gui.tabs.prescriptions_tab import PrescriptionsTab
from app.gui.tabs.registry_tab import RegistryTab
from app.gui.tabs.reporting_tab import ReportingTab
from app.gui.tabs.timeline_tab import TimelineTab
from app.gui.tabs.visits_tab import VisitsTab
from app.gui.tabs.vitals_tab import VitalsTab

# (internal key, translation key, tab class) - internal keys are stable and
# language-independent so code/tests never depend on translated display text.
PATIENT_TABS = [
    ("registry", "tab.registry", RegistryTab),
    ("history", "tab.history", HistoryTab),
    ("visits", "tab.visits", VisitsTab),
    ("vitals", "tab.vitals", VitalsTab),
    ("diagnoses", "tab.diagnoses", DiagnosesTab),
    ("orders", "tab.orders", OrdersTab),
    ("prescriptions", "tab.prescriptions", PrescriptionsTab),
    ("plans", "tab.plans", PlansTab),
    ("appointments", "tab.appointments", AppointmentsTab),
    ("documents", "tab.documents", DocumentsTab),
    ("billing", "tab.billing", BillingTab),
    ("timeline", "tab.timeline", TimelineTab),
]


class MainWindow(ttk.Frame):
    """Acts as the shared `ctx` object passed to every tab: exposes `.db`,
    `.current_patient_id`, `.require_patient()`, `.audit()` and `.t()`."""

    def __init__(self, root: tk.Tk, db: Database, current_user: dict):
        super().__init__(root)
        self.root = root
        self.db = db
        self.current_user = current_user
        self.on_logout = None
        self._current_patient_id: int | None = None
        self.pack(fill="both", expand=True)
        self._build()
        self.dashboard_tab.refresh()

    # ------------------------------------------------------------- ctx api
    @property
    def current_patient_id(self) -> int | None:
        return self._current_patient_id

    def require_patient(self) -> int:
        if self._current_patient_id is None:
            raise ValueError(t("common.no_patient_message"))
        return self._current_patient_id

    def set_current_patient(self, patient_id: int | None):
        self._current_patient_id = patient_id
        self._refresh_patient_header()
        self._reload_all_tabs()

    def on_patient_saved(self):
        self._refresh_patient_search()
        self._refresh_patient_header()

    def audit(self, action, entity_type=None, entity_id=None, details=None):
        audit_dao.log_action(
            self.db, action, entity_type=entity_type, entity_id=entity_id, details=details,
            user_id=self.current_user["id"], username=self.current_user["username"],
        )

    # ------------------------------------------------------------- layout
    def _build(self):
        self._build_header()

        self.master_pane = ttk.PanedWindow(self, orient="horizontal")
        self.master_pane.pack(fill="both", expand=True)

        sidebar = ttk.Frame(self.master_pane, width=260)
        self.master_pane.add(sidebar, weight=1)
        self._build_sidebar(sidebar)

        right = ttk.Frame(self.master_pane)
        self.master_pane.add(right, weight=4)
        self._build_right(right)

        status = ttk.Frame(self, style="StatusBar.TFrame")
        status.pack(fill="x", side="bottom")
        self.patient_label = ttk.Label(status, style="StatusBar.TLabel", anchor="w")
        self.patient_label.pack(side="left", padx=10, pady=4)
        self._refresh_patient_header()

    def _build_header(self):
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text=t("app.title"), style="Header.TLabel").pack(
            side="left", padx=20, pady=14
        )
        right = ttk.Frame(header, style="Header.TFrame")
        right.pack(side="right", padx=20, pady=14)
        ttk.Label(
            right,
            text=t("main.signed_in_as", name=self.current_user["full_name"],
                    role=t(f"role.{self.current_user['role']}")),
            style="HeaderSubtitle.TLabel",
        ).pack(side="left", padx=(0, 14))
        ttk.Button(
            right, text=t("main.log_out"), style="outline.TButton", command=self._log_out,
        ).pack(side="left")

    def _build_sidebar(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        ttk.Label(parent, text=t("main.patient_search"), font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=(10, 0)
        )
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(parent, textvariable=self.search_var)
        search_entry.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        search_entry.bind("<KeyRelease>", lambda e: self._refresh_patient_search())

        self.patient_list = tk.Listbox(parent, exportselection=False, borderwidth=1,
                                        highlightthickness=1, relief="solid")
        self.patient_list.grid(row=2, column=0, sticky="nsew", padx=8)
        self.patient_list.bind("<<ListboxSelect>>", self._on_patient_selected)
        self._patient_list_ids: list[int] = []

        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=8)
        ttk.Button(btn_frame, text=t("main.new_patient"), style="primary.TButton",
                   command=self._new_patient).pack(side="top", fill="x", pady=(0, 4))
        ttk.Button(btn_frame, text=t("main.backup_now"), style="outline.TButton",
                   command=self._backup_now).pack(side="top", fill="x")

        ttk.Separator(parent, orient="horizontal").grid(row=4, column=0, sticky="ew", padx=8, pady=(6, 10))

        ttk.Label(parent, text=t("main.full_text_search"), font=("Helvetica", 10, "bold")).grid(
            row=5, column=0, sticky="w", padx=8
        )
        self.fts_var = tk.StringVar()
        fts_entry = ttk.Entry(parent, textvariable=self.fts_var)
        fts_entry.grid(row=6, column=0, sticky="ew", padx=8, pady=6)
        fts_entry.bind("<Return>", lambda e: self._run_full_text_search())
        self.fts_results = tk.Listbox(parent, height=8, exportselection=False, borderwidth=1,
                                       highlightthickness=1, relief="solid")
        self.fts_results.grid(row=7, column=0, sticky="nsew", padx=8, pady=(0, 10))
        self.fts_results.bind("<<ListboxSelect>>", self._on_fts_result_selected)
        self._fts_result_patients: list[int | None] = []

        self._refresh_patient_search()

    def _build_right(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.dashboard_tab = DashboardTab(self.notebook, self)
        self.notebook.add(self.dashboard_tab, text=t("tab.dashboard"))

        self._tab_instances: dict[str, ttk.Frame] = {}
        for key, translation_key, cls in PATIENT_TABS:
            instance = cls(self.notebook, self)
            self.notebook.add(instance, text=t(translation_key))
            self._tab_instances[key] = instance

        self.reporting_tab = ReportingTab(self.notebook, self)
        self.notebook.add(self.reporting_tab, text=t("tab.reporting"))

        if self.current_user.get("role") == "admin":
            self.admin_tab = AdminTab(self.notebook, self)
            self.notebook.add(self.admin_tab, text=t("tab.admin"))
            self.admin_tab.refresh()

    # ------------------------------------------------------------- actions
    def _log_out(self):
        if self.on_logout:
            self.on_logout()

    def _refresh_patient_search(self):
        term = self.search_var.get().strip()
        self.patient_list.delete(0, "end")
        self._patient_list_ids = []
        rows = patients_dao.search_patients(self.db, term) if term else patients_dao.list_patients(self.db)
        for row in rows:
            self.patient_list.insert(
                "end", f"{row['last_name']}, {row['first_name']} ({row['mrn']})"
            )
            self._patient_list_ids.append(row["id"])

    def _on_patient_selected(self, _event=None):
        selection = self.patient_list.curselection()
        if not selection:
            return
        patient_id = self._patient_list_ids[selection[0]]
        self.set_current_patient(patient_id)

    def _new_patient(self):
        self.set_current_patient(None)
        self.notebook.select(self._tab_instances["registry"])

    def _reload_all_tabs(self):
        for instance in self._tab_instances.values():
            instance.load_patient()
        self.reporting_tab.load_patient()
        if hasattr(self, "admin_tab"):
            self.admin_tab.load_patient()

    def _refresh_patient_header(self):
        if self._current_patient_id is None:
            self.patient_label.configure(text=t("main.no_patient_selected"))
            return
        row = patients_dao.get_patient(self.db, self._current_patient_id)
        if row is None:
            self.patient_label.configure(text=t("main.no_patient_selected"))
            return
        self.patient_label.configure(
            text=t("main.patient_header", first=row["first_name"], last=row["last_name"],
                   mrn=row["mrn"], dob=row["dob"])
        )

    def _backup_now(self):
        path = self.db.backup()
        self.audit("BACKUP", details=str(path))
        messagebox.showinfo(t("main.backup_done_title"), t("main.backup_done_message", path=path))

    def _run_full_text_search(self):
        term = self.fts_var.get().strip()
        self.fts_results.delete(0, "end")
        self._fts_result_patients = []
        if not term:
            return
        for row in search_dao.full_text_search(self.db, term):
            label = f"[{row['entity_type']}] {row['title']}"
            self.fts_results.insert("end", label)
            self._fts_result_patients.append(row["patient_id"])

    def _on_fts_result_selected(self, _event=None):
        selection = self.fts_results.curselection()
        if not selection:
            return
        patient_id = self._fts_result_patients[selection[0]]
        if patient_id is not None:
            self.set_current_patient(patient_id)
