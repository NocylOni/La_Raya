"""Login dialog (Module 13: User & Security)."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.db.dao import users as users_dao


class LoginDialog(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("Patient Management - Sign In")
        self.resizable(False, False)
        self.result_user = None
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky="e", pady=4)
        self.username_entry = ttk.Entry(frame, width=24)
        self.username_entry.grid(row=0, column=1, pady=4)
        self.username_entry.focus_set()

        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="e", pady=4)
        self.password_entry = ttk.Entry(frame, width=24, show="*")
        self.password_entry.grid(row=1, column=1, pady=4)
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())

        self.error_label = ttk.Label(frame, text="", foreground="red")
        self.error_label.grid(row=2, column=0, columnspan=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(8, 0))
        ttk.Button(btn_frame, text="Sign In", command=self._attempt_login).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self._cancel).pack(side="left", padx=4)

        self.grab_set()

    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        result = users_dao.authenticate(self.db, username, password)
        if not result.success:
            self.error_label.configure(text=result.message or "Login failed")
            return
        self.result_user = result.user
        self.destroy()

    def _cancel(self):
        self.result_user = None
        self.destroy()
