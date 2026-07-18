"""Login dialog: credentials + language switcher (Module 13: User & Security)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.db.dao import users as users_dao
from app.i18n import LANGUAGES, get_language, set_language, t


class LoginDialog(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.result_user = None
        self.resizable(False, False)
        self.configure(background="white")
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._build()
        self._apply_translations()
        self.username_entry.focus_set()
        self.grab_set()

    # ------------------------------------------------------------- layout
    def _build(self):
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x")
        self.title_label = ttk.Label(header, style="Header.TLabel")
        self.title_label.pack(padx=28, pady=(22, 2), anchor="w")
        self.subtitle_label = ttk.Label(header, style="HeaderSubtitle.TLabel")
        self.subtitle_label.pack(padx=28, pady=(0, 18), anchor="w")

        body = ttk.Frame(self, padding=28)
        body.pack(fill="both", expand=True)

        lang_row = ttk.Frame(body)
        lang_row.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
        self.lang_label = ttk.Label(lang_row)
        self.lang_label.pack(side="left", padx=(0, 8))
        self._lang_buttons: dict[str, ttk.Button] = {}
        for code, name in LANGUAGES.items():
            btn = ttk.Button(
                lang_row, text=name, width=10,
                command=lambda c=code: self._select_language(c),
            )
            btn.pack(side="left", padx=2)
            self._lang_buttons[code] = btn

        self.username_label = ttk.Label(body)
        self.username_label.grid(row=1, column=0, sticky="e", pady=6, padx=(0, 8))
        self.username_entry = ttk.Entry(body, width=26)
        self.username_entry.grid(row=1, column=1, pady=6, sticky="w")

        self.password_label = ttk.Label(body)
        self.password_label.grid(row=2, column=0, sticky="e", pady=6, padx=(0, 8))
        self.password_entry = ttk.Entry(body, width=26, show="•")
        self.password_entry.grid(row=2, column=1, pady=6, sticky="w")
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())

        self.error_label = ttk.Label(body, foreground="#c0392b")
        self.error_label.grid(row=3, column=0, columnspan=2, pady=(4, 0))

        btn_frame = ttk.Frame(body)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(18, 4))
        self.sign_in_button = ttk.Button(
            btn_frame, command=self._attempt_login, style="success.TButton", width=14,
        )
        self.sign_in_button.pack(side="left", padx=4)
        self.cancel_button = ttk.Button(
            btn_frame, command=self._cancel, style="secondary.TButton", width=14,
        )
        self.cancel_button.pack(side="left", padx=4)

        self.hint_label = ttk.Label(body, foreground="#8a8a8a", font=("Helvetica", 8))
        self.hint_label.grid(row=5, column=0, columnspan=2, pady=(14, 0))

    # --------------------------------------------------------- translation
    def _select_language(self, code: str):
        set_language(code)
        self._apply_translations()

    def _apply_translations(self):
        active = get_language()
        self.title(t("login.window_title"))
        self.title_label.configure(text=t("app.title"))
        self.subtitle_label.configure(text=t("login.subtitle"))
        self.lang_label.configure(text=t("login.language"))
        for code, btn in self._lang_buttons.items():
            btn.configure(style="primary.TButton" if code == active else "outline.TButton")
        self.username_label.configure(text=t("login.username"))
        self.password_label.configure(text=t("login.password"))
        self.sign_in_button.configure(text=t("login.sign_in"))
        self.cancel_button.configure(text=t("login.cancel"))
        self.hint_label.configure(text=t("login.default_admin_hint"))

    # ------------------------------------------------------------- actions
    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        result = users_dao.authenticate(self.db, username, password)
        if not result.success:
            self.error_label.configure(text=t("login.error_invalid"))
            return
        user_language = result.user.get("language") or get_language()
        set_language(user_language)
        self.result_user = result.user
        self.destroy()

    def _cancel(self):
        self.result_user = None
        self.destroy()
