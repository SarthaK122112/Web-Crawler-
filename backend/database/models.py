"""
Database models and initialization.

Uses SQLite for persistent storage of audit tasks, crawled pages,
and detected dark patterns. Provides helper functions for CRUD operations.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "dark_patterns.db")


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_db():
    """Create all required database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS audits (
            task_id         TEXT PRIMARY KEY,
            url             TEXT NOT NULL,
            topic           TEXT NOT NULL,
            max_pages       INTEGER DEFAULT 20,
            threshold        REAL DEFAULT 0.3,
            status          TEXT DEFAULT 'pending',
            pages_crawled   INTEGER DEFAULT 0,
            pages_total     INTEGER DEFAULT 0,
            patterns_found  INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS crawled_pages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         TEXT NOT NULL,
            url             TEXT NOT NULL,
            title           TEXT,
            relevance_score REAL DEFAULT 0.0,
            content_length  INTEGER DEFAULT 0,
            crawled_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (task_id) REFERENCES audits(task_id)
        );

        CREATE TABLE IF NOT EXISTS detected_patterns (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         TEXT NOT NULL,
            page_url        TEXT NOT NULL,
            pattern_type    TEXT NOT NULL,
            description     TEXT,
            confidence      REAL DEFAULT 0.0,
            evidence        TEXT,
            method          TEXT DEFAULT 'rule-based',
            detected_at     TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (task_id) REFERENCES audits(task_id)
        );

        CREATE TABLE IF NOT EXISTS screenshots (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         TEXT NOT NULL,
            page_url        TEXT NOT NULL,
            filepath        TEXT NOT NULL,
            analysis_result TEXT,
            captured_at     TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (task_id) REFERENCES audits(task_id)
        );

        CREATE TABLE IF NOT EXISTS graph_edges (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id         TEXT NOT NULL,
            source_url      TEXT NOT NULL,
            target_url      TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES audits(task_id)
        );
    """)

    conn.commit()
    conn.close()


# ── Audit CRUD ──────────────────────────────────────────────

def create_audit(task_id: str, url: str, topic: str, max_pages: int, threshold: float):
    """Insert a new audit record."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audits (task_id, url, topic, max_pages, threshold, status) VALUES (?, ?, ?, ?, ?, 'running')",
        (task_id, url, topic, max_pages, threshold),
    )
    conn.commit()
    conn.close()


def update_audit_status(task_id: str, status: str, pages_crawled: int = None, patterns_found: int = None):
    """Update audit progress fields."""
    conn = get_connection()
    fields = ["status = ?", "updated_at = datetime('now')"]
    params = [status]

    if pages_crawled is not None:
        fields.append("pages_crawled = ?")
        params.append(pages_crawled)
    if patterns_found is not None:
        fields.append("patterns_found = ?")
        params.append(patterns_found)

    params.append(task_id)
    conn.execute(f"UPDATE audits SET {', '.join(fields)} WHERE task_id = ?", params)
    conn.commit()
    conn.close()


def get_audit(task_id: str) -> Optional[dict]:
    """Retrieve an audit record by task_id."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM audits WHERE task_id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Crawled Pages ───────────────────────────────────────────

def insert_crawled_page(task_id: str, url: str, title: str, relevance_score: float, content_length: int):
    """Store a crawled page result."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO crawled_pages (task_id, url, title, relevance_score, content_length) VALUES (?, ?, ?, ?, ?)",
        (task_id, url, title, relevance_score, content_length),
    )
    conn.commit()
    conn.close()


def get_crawled_pages(task_id: str) -> list:
    """Retrieve all crawled pages for an audit."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM crawled_pages WHERE task_id = ? ORDER BY relevance_score DESC", (task_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Dark Patterns ───────────────────────────────────────────

def insert_pattern(task_id: str, page_url: str, pattern_type: str,
                   description: str, confidence: float, evidence: str, method: str = "rule-based"):
    """Store a detected dark pattern."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO detected_patterns (task_id, page_url, pattern_type, description, confidence, evidence, method) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (task_id, page_url, pattern_type, description, confidence, evidence, method),
    )
    conn.commit()
    conn.close()


def get_patterns(task_id: str) -> list:
    """Retrieve all detected patterns for an audit."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM detected_patterns WHERE task_id = ? ORDER BY confidence DESC", (task_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Screenshots ─────────────────────────────────────────────

def insert_screenshot(task_id: str, page_url: str, filepath: str, analysis_result: str = None):
    """Store screenshot metadata."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO screenshots (task_id, page_url, filepath, analysis_result) VALUES (?, ?, ?, ?)",
        (task_id, page_url, filepath, analysis_result),
    )
    conn.commit()
    conn.close()


def get_screenshots(task_id: str) -> list:
    """Retrieve all screenshots for an audit."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM screenshots WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Graph Edges ─────────────────────────────────────────────

def insert_edge(task_id: str, source_url: str, target_url: str):
    """Store a hyperlink edge between two crawled pages."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO graph_edges (task_id, source_url, target_url) VALUES (?, ?, ?)",
        (task_id, source_url, target_url),
    )
    conn.commit()
    conn.close()


def get_edges(task_id: str) -> list:
    """Retrieve all graph edges for an audit."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM graph_edges WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
