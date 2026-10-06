"""
Credential store for WebAuthn / FIDO2 biometric second factor.

Stores ONLY public keys + metadata. No biometric data ever reaches the server:
the fingerprint / face match happens inside the user's device, and the device
just signs a challenge.

Storage: SQLite (stdlib, free). Path is controlled by WEBAUTHN_DB_PATH.
NOTE: on Vercel the filesystem is ephemeral (/tmp), so enrolled credentials
vanish on cold starts. For a persistent deployment point this at a free
hosted database instead (see INTEGRATION.md).
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("WEBAUTHN_DB_PATH") or (
    "/tmp/webauthn.db" if os.environ.get("VERCEL") else os.path.join(_BASE, "webauthn.db")
)


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    with _conn() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS webauthn_credentials (
                credential_id TEXT PRIMARY KEY,      -- base64url
                username      TEXT NOT NULL,
                public_key    BLOB NOT NULL,
                sign_count    INTEGER NOT NULL DEFAULT 0,
                device_label  TEXT,
                created_at    TEXT NOT NULL,
                last_used_at  TEXT
            )
            """
        )
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_wa_user ON webauthn_credentials(username)"
        )


def list_credentials(username):
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM webauthn_credentials WHERE username = ? ORDER BY created_at",
            (username,),
        ).fetchall()
    return [dict(r) for r in rows]


def has_credentials(username):
    with _conn() as con:
        row = con.execute(
            "SELECT 1 FROM webauthn_credentials WHERE username = ? LIMIT 1", (username,)
        ).fetchone()
    return row is not None


def get_credential(credential_id):
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM webauthn_credentials WHERE credential_id = ?", (credential_id,)
        ).fetchone()
    return dict(row) if row else None


def add_credential(username, credential_id, public_key, sign_count, label):
    with _conn() as con:
        con.execute(
            """
            INSERT INTO webauthn_credentials
                (credential_id, username, public_key, sign_count, device_label, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (credential_id, username, public_key, sign_count, label, _now()),
        )


def update_usage(credential_id, sign_count):
    with _conn() as con:
        con.execute(
            "UPDATE webauthn_credentials SET sign_count = ?, last_used_at = ? WHERE credential_id = ?",
            (sign_count, _now(), credential_id),
        )


def delete_credential(username, credential_id):
    with _conn() as con:
        cur = con.execute(
            "DELETE FROM webauthn_credentials WHERE credential_id = ? AND username = ?",
            (credential_id, username),
        )
    return cur.rowcount > 0
