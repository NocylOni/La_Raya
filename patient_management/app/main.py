"""Application entry point."""
from __future__ import annotations

from app.db.database import Database
from app.db.dao import users as users_dao
from app.gui import theme
from app.gui.login import LoginDialog
from app.gui.main_window import MainWindow
from app.i18n import t


def main() -> None:
    db = Database()
    users_dao.ensure_default_admin(db)

    root = theme.create_root()
    root.withdraw()

    while True:
        login = LoginDialog(root, db)
        root.wait_window(login)
        if login.result_user is None:
            break

        root.title(t("app.title"))
        root.deiconify()
        root.geometry("1440x850")
        root.minsize(1150, 700)

        win = MainWindow(root, db, login.result_user)
        logged_out = {"value": False}

        def _handle_logout():
            logged_out["value"] = True
            root.quit()

        win.on_logout = _handle_logout
        root.protocol("WM_DELETE_WINDOW", root.quit)
        root.mainloop()
        win.destroy()

        if not logged_out["value"]:
            break
        root.withdraw()

    root.destroy()


if __name__ == "__main__":
    main()
