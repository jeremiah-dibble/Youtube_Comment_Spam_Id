import sqlite3
from typing import Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "banned_authors.sqlite")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS banned_authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            evidence TEXT,
            banned_by TEXT NOT NULL,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_banned_author(author_id: str, reason: str, evidence: str, banned_by: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO banned_authors (author_id, reason, evidence, banned_by) VALUES (?, ?, ?, ?)",
        (author_id, reason, evidence, banned_by)
    )
    conn.commit()
    conn.close()

def is_author_banned(author_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM banned_authors WHERE author_id = ?", (author_id,))
    result = c.fetchone()
    conn.close()
    return result is not None
