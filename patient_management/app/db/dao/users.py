"""User accounts, roles and authentication (Module 13: User & Security)."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from app.db.database import Database

ROLES = ("admin", "physician", "nurse", "clinician", "front_desk", "billing")

PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    ).hex()


def _make_salt() -> str:
    return os.urandom(16).hex()


@dataclass
class AuthResult:
    success: bool
    user: dict | None = None
    message: str = ""


def create_user(
    db: Database, username: str, password: str, full_name: str, role: str = "clinician"
) -> int:
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")
    if not username or not password:
        raise ValueError("Username and password are required")
    salt = _make_salt()
    pw_hash = _hash_password(password, salt)
    return db.execute(
        "INSERT INTO users(username, password_hash, salt, full_name, role) "
        "VALUES (?, ?, ?, ?, ?)",
        (username.strip(), pw_hash, salt, full_name.strip(), role),
    )


def authenticate(db: Database, username: str, password: str) -> AuthResult:
    row = db.query_one(
        "SELECT * FROM users WHERE username = ? AND active = 1", (username.strip(),)
    )
    if row is None:
        return AuthResult(False, message="Invalid username or password")
    expected = _hash_password(password, row["salt"])
    if expected != row["password_hash"]:
        return AuthResult(False, message="Invalid username or password")
    db.execute(
        "UPDATE users SET last_login = datetime('now') WHERE id = ?", (row["id"],)
    )
    return AuthResult(True, user=dict(row))


def set_password(db: Database, user_id: int, new_password: str) -> None:
    salt = _make_salt()
    pw_hash = _hash_password(new_password, salt)
    db.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (pw_hash, salt, user_id),
    )


def set_active(db: Database, user_id: int, active: bool) -> None:
    db.execute("UPDATE users SET active = ? WHERE id = ?", (1 if active else 0, user_id))


def list_users(db: Database) -> list:
    return db.query("SELECT id, username, full_name, role, active, created_at, last_login "
                     "FROM users ORDER BY username")


def get_user(db: Database, user_id: int):
    return db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))


def ensure_default_admin(db: Database) -> None:
    """Create a default admin account if no users exist yet."""
    row = db.query_one("SELECT COUNT(*) AS n FROM users")
    if row["n"] == 0:
        create_user(db, "admin", "admin123", "Administrator", role="admin")
