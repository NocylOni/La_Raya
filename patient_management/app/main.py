"""Application entry point."""
from __future__ import annotations

import tkinter as tk

from app.db.database import Database
from app.db.dao import users as users_dao
from app.gui.login import LoginDialog
from app.gui.main_window import MainWindow


def main() -> None:
    db = Database()
    users_dao.ensure_default_admin(db)

    root = tk.Tk()
    root.withdraw()
    root.title("Patient Management System")

    login = LoginDialog(root, db)
    root.wait_window(login)

    if login.result_user is None:
        root.destroy()
        return

    root.deiconify()
    root.geometry("1200x750")
    root.minsize(1000, 650)
    MainWindow(root, db, login.result_user)
    root.mainloop()


if __name__ == "__main__":
    main()
