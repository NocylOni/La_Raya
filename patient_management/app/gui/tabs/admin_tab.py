"""Module 13: User & Security tab (accounts, roles, audit log, backups)."""
from __future__ import annotations

from tkinter import messagebox, ttk

from app.db.dao import audit as audit_dao
from app.db.dao import users as users_dao
from app.gui.widgets import FieldSpec, RecordPanel, clean_form_values


class AdminTab(ttk.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        ttk.Button(toolbar, text="Backup Database Now", command=self._backup_now).pack(side="left")
        ttk.Button(toolbar, text="Refresh Audit Log", command=self._refresh_audit).pack(
            side="left", padx=6
        )

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        self.users_panel = RecordPanel(
            nb,
            columns=[("username", "Username"), ("full_name", "Full Name"),
                     ("role", "Role"), ("active", "Active")],
            fields=[
                FieldSpec("username", "Username"),
                FieldSpec("full_name", "Full Name"),
                FieldSpec("password", "Password (new users only)"),
                FieldSpec("role", "Role", kind="combo", options=list(users_dao.ROLES)),
            ],
            on_list=lambda: users_dao.list_users(self.ctx.db),
            on_create=self._create_user,
        )
        nb.add(self.users_panel, text="User Accounts")

        audit_frame = ttk.Frame(nb)
        audit_frame.columnconfigure(0, weight=1)
        audit_frame.rowconfigure(0, weight=1)
        self.audit_tree = ttk.Treeview(
            audit_frame, columns=("timestamp", "username", "action", "entity", "details"),
            show="headings",
        )
        for key, header in (("timestamp", "When"), ("username", "User"), ("action", "Action"),
                             ("entity", "Entity"), ("details", "Details")):
            self.audit_tree.heading(key, text=header)
            self.audit_tree.column(key, width=130)
        self.audit_tree.grid(row=0, column=0, sticky="nsew")
        nb.add(audit_frame, text="Audit Log")

    def load_patient(self):
        pass  # clinic-wide admin tab, not patient-scoped

    def refresh(self):
        self.users_panel.refresh()
        self._refresh_audit()

    def _create_user(self, data):
        data = clean_form_values(data)
        username = data.pop("username")
        password = data.pop("password") or "changeme123"
        full_name = data.pop("full_name")
        role = data.pop("role") or "clinician"
        user_id = users_dao.create_user(self.ctx.db, username, password, full_name, role=role)
        self.ctx.audit("CREATE_USER", "user", user_id, username)
        return user_id

    def _refresh_audit(self):
        for row in self.audit_tree.get_children():
            self.audit_tree.delete(row)
        for row in audit_dao.list_audit_log(self.ctx.db):
            entity = f"{row['entity_type'] or ''} #{row['entity_id']}" if row["entity_id"] else (row["entity_type"] or "")
            self.audit_tree.insert(
                "", "end",
                values=(row["timestamp"], row["username"] or "", row["action"], entity,
                        row["details"] or ""),
            )

    def _backup_now(self):
        path = self.ctx.db.backup()
        self.ctx.audit("BACKUP", details=str(path))
        messagebox.showinfo("Backup complete", f"Database backed up to:\n{path}")
