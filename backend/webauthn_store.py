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
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("WEBAUTHN_DB_PATH") or (
    os.path.join(tempfile.gettempdir(), "webauthn.db") if (os.environ.get("VERCEL") or not os.access(_BASE, os.W_OK)) else os.path.join(_BASE, "webauthn.db")
)

# Resilient in-memory store for serverless environments
_IN_MEMORY_CREDS = {}


@contextmanager
def _conn():
    try:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()
    except Exception:
        yield None


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    with _conn() as con:
        if con:
            try:
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
            except Exception:
                pass


# Initialize DB on load
try:
    init_db()
except Exception:
    pass


def list_credentials(username):
    results = []
    # 1. From SQLite
    with _conn() as con:
        if con:
            try:
                rows = con.execute(
                    "SELECT * FROM webauthn_credentials WHERE username = ? ORDER BY created_at",
                    (username,),
                ).fetchall()
                results = [dict(r) for r in rows]
            except Exception:
                pass
    # 2. Sync from in-memory if empty
    if not results and username in _IN_MEMORY_CREDS:
        results = list(_IN_MEMORY_CREDS[username].values())
    return results


def has_credentials(username):
    if username in _IN_MEMORY_CREDS and len(_IN_MEMORY_CREDS[username]) > 0:
        return True
    with _conn() as con:
        if con:
            try:
                row = con.execute(
                    "SELECT 1 FROM webauthn_credentials WHERE username = ? LIMIT 1", (username,)
                ).fetchone()
                return row is not None
            except Exception:
                pass
    return False


def get_credential(credential_id):
    # 1. Check in-memory
    for user_creds in _IN_MEMORY_CREDS.values():
        if credential_id in user_creds:
            return user_creds[credential_id]
    # 2. Check SQLite
    with _conn() as con:
        if con:
            try:
                row = con.execute(
                    "SELECT * FROM webauthn_credentials WHERE credential_id = ?", (credential_id,)
                ).fetchone()
                if row:
                    return dict(row)
            except Exception:
                pass
    return None


def add_credential(username, credential_id, public_key, sign_count, label):
    cred_data = {
        "credential_id": credential_id,
        "username": username,
        "public_key": public_key,
        "sign_count": sign_count,
        "device_label": label,
        "created_at": _now(),
        "last_used_at": None
    }
    if username not in _IN_MEMORY_CREDS:
        _IN_MEMORY_CREDS[username] = {}
    _IN_MEMORY_CREDS[username][credential_id] = cred_data

    with _conn() as con:
        if con:
            try:
                con.execute(
                    """
                    INSERT INTO webauthn_credentials
                        (credential_id, username, public_key, sign_count, device_label, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (credential_id, username, public_key, sign_count, label, _now()),
                )
            except Exception:
                pass


def update_usage(credential_id, sign_count):
    for user_creds in _IN_MEMORY_CREDS.values():
        if credential_id in user_creds:
            user_creds[credential_id]["sign_count"] = sign_count
            user_creds[credential_id]["last_used_at"] = _now()

    with _conn() as con:
        if con:
            try:
                con.execute(
                    "UPDATE webauthn_credentials SET sign_count = ?, last_used_at = ? WHERE credential_id = ?",
                    (sign_count, _now(), credential_id),
                )
            except Exception:
                pass


def delete_credential(username, credential_id):
    if username in _IN_MEMORY_CREDS and credential_id in _IN_MEMORY_CREDS[username]:
        del _IN_MEMORY_CREDS[username][credential_id]

    with _conn() as con:
        if con:
            try:
                cur = con.execute(
                    "DELETE FROM webauthn_credentials WHERE credential_id = ? AND username = ?",
                    (credential_id, username),
                )
                return cur.rowcount > 0
            except Exception:
                pass
    return True
