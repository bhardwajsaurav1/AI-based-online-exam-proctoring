"""
Database Management Adapter.
Author: Sole Contributor / Creator
Supports automatic SQLite initialization, serverless fallback, and MySQL database connectivity.
"""

import sqlite3
import hashlib
import tempfile
import os
from pathlib import Path
import config

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

# Resilient in-memory user registry for serverless environments
IN_MEMORY_USERS = {
    "student1": {
        "id": 1,
        "username": "student1",
        "email": "student1@exam.org",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest()
    }
}

class Database:
    def __init__(self, db_type=config.DATABASE_TYPE):
        self.db_type = db_type
        # Determine writable SQLite path
        try:
            self.sqlite_path = Path(tempfile.gettempdir()) / "proctoring.db"
        except Exception:
            self.sqlite_path = config.SQLITE_DB_PATH
        self._init_db()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _init_db(self):
        """Initializes tables for candidates, credentials, exams, and logs."""
        if self.db_type == "sqlite":
            try:
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        exam_title TEXT NOT NULL,
                        score INTEGER DEFAULT 0,
                        total_violations INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'IN_PROGRESS',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )
                ''')
                # Seed default demo candidate if table empty
                cursor.execute("SELECT COUNT(*) FROM users")
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                        ("student1", "student1@exam.org", self._hash_password("password123"))
                    )
                conn.commit()
                conn.close()
                print(f"[✓] Database: SQLite initialized at {self.sqlite_path}")
            except Exception as e:
                print(f"[Warning] SQLite init notice (using resilient memory registry): {e}")

        elif self.db_type == "mysql" and HAS_MYSQL:
            try:
                cnx = mysql.connector.connect(**config.MYSQL_CONFIG)
                cursor = cnx.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sign_up (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cnx.commit()
                cursor.close()
                cnx.close()
                print("[✓] Database: MySQL connection initialized successfully.")
            except Exception as e:
                print(f"[Warning] Database: MySQL connection failed, falling back to SQLite: {e}")
                self.db_type = "sqlite"
                self._init_db()

    def register_user(self, email, username, password):
        """Registers a new candidate account."""
        if not email or not username or not password:
            return False

        username = username.strip().lower()
        email = email.strip().lower()
        pwd_hash = self._hash_password(password)

        # Check in-memory existence
        if username in IN_MEMORY_USERS:
            return False
        for u in IN_MEMORY_USERS.values():
            if u["email"] == email:
                return False

        # Store in-memory
        user_id = len(IN_MEMORY_USERS) + 1
        IN_MEMORY_USERS[username] = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": pwd_hash
        }

        # Also attempt persistent storage
        try:
            if self.db_type == "sqlite":
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
                    (email, username, pwd_hash)
                )
                conn.commit()
                conn.close()
            elif self.db_type == "mysql" and HAS_MYSQL:
                cnx = mysql.connector.connect(**config.MYSQL_CONFIG)
                cursor = cnx.cursor()
                cursor.execute(
                    "INSERT INTO sign_up (email, username, password) VALUES (%s, %s, %s)",
                    (email, username, pwd_hash)
                )
                cnx.commit()
                cursor.close()
                cnx.close()
        except Exception:
            pass

        return True

    def authenticate_user(self, username, password):
        """Verifies candidate credentials."""
        if not username or not password:
            return None

        username_input = username.strip().lower()
        pwd_hash = self._hash_password(password)

        # 1. Check in-memory registry
        for u in IN_MEMORY_USERS.values():
            if (u["username"] == username_input or u["email"] == username_input) and u["password_hash"] == pwd_hash:
                return {"id": u["id"], "username": u["username"], "email": u["email"]}

        # 2. Check SQLite persistent database
        try:
            if self.db_type == "sqlite":
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, email FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
                    (username_input, username_input, pwd_hash)
                )
                user = cursor.fetchone()
                conn.close()
                if user:
                    # Sync into memory
                    IN_MEMORY_USERS[user[1]] = {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "password_hash": pwd_hash
                    }
                    return {"id": user[0], "username": user[1], "email": user[2]}
            elif self.db_type == "mysql" and HAS_MYSQL:
                cnx = mysql.connector.connect(**config.MYSQL_CONFIG)
                cursor = cnx.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, username, email FROM sign_up WHERE (username = %s OR email = %s) AND password = %s",
                    (username_input, username_input, pwd_hash)
                )
                user = cursor.fetchone()
                cursor.close()
                cnx.close()
                if user:
                    return user
        except Exception:
            pass

        return None
