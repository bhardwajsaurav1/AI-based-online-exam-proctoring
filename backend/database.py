"""
Database Management Adapter.
Author: Sole Contributor / Creator
Supports automatic SQLite initialization and optional MySQL database connectivity.
"""

import sqlite3
import hashlib
import config

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

class Database:
    def __init__(self, db_type=config.DATABASE_TYPE):
        self.db_type = db_type
        self._init_db()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _init_db(self):
        """Initializes tables for candidates, credentials, exams, and logs."""
        if self.db_type == "sqlite":
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
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
            print(f"[✓] Database: SQLite initialized at {config.SQLITE_DB_PATH}")

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
        pwd_hash = self._hash_password(password)
        try:
            if self.db_type == "sqlite":
                conn = sqlite3.connect(config.SQLITE_DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
                    (email, username, pwd_hash)
                )
                conn.commit()
                conn.close()
                return True
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
                return True
        except Exception as e:
            print(f"[Error] Register User Failed: {e}")
            return False
        return False

    def authenticate_user(self, username, password):
        """Verifies candidate credentials."""
        pwd_hash = self._hash_password(password)
        try:
            if self.db_type == "sqlite":
                conn = sqlite3.connect(config.SQLITE_DB_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, email FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
                    (username, username, pwd_hash)
                )
                user = cursor.fetchone()
                conn.close()
                if user:
                    return {"id": user[0], "username": user[1], "email": user[2]}
                return None
            elif self.db_type == "mysql" and HAS_MYSQL:
                cnx = mysql.connector.connect(**config.MYSQL_CONFIG)
                cursor = cnx.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, username, email FROM sign_up WHERE (username = %s OR email = %s) AND password = %s",
                    (username, username, pwd_hash)
                )
                user = cursor.fetchone()
                cursor.close()
                cnx.close()
                return user
        except Exception as e:
            print(f"[Error] Authenticate User Failed: {e}")
            return None
        return None
