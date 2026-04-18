"""SQLite 数据库存储（Android 兼容版）"""

import sqlite3
import os

# Android 上使用 app 私有目录
try:
    from android.storage import app_storage_path
    DB_DIR = app_storage_path()
except ImportError:
    DB_DIR = os.path.dirname(__file__)

DB_PATH = os.path.join(DB_DIR, "data.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS printers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sn TEXT UNIQUE NOT NULL,
            key TEXT DEFAULT '',
            name TEXT DEFAULT '',
            purpose TEXT DEFAULT 'receipt',
            is_default INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cup_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            enabled INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


# ===== 打印机操作 =====

def add_printer(sn, key="", name="", purpose="receipt", is_default=False):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO printers (sn, key, name, purpose, is_default) VALUES (?,?,?,?,?)",
            (sn, key, name, purpose, 1 if is_default else 0),
        )
        if is_default:
            conn.execute(
                "UPDATE printers SET is_default=0 WHERE purpose=? AND sn!=?",
                (purpose, sn),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def get_printers(purpose=None):
    conn = get_conn()
    try:
        if purpose:
            rows = conn.execute("SELECT * FROM printers WHERE purpose=?", (purpose,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM printers").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_default_printer(purpose="receipt"):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM printers WHERE purpose=? AND is_default=1 LIMIT 1", (purpose,)
        ).fetchone()
        if row:
            return dict(row)
        row = conn.execute(
            "SELECT * FROM printers WHERE purpose=? LIMIT 1", (purpose,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_printer(sn):
    conn = get_conn()
    conn.execute("DELETE FROM printers WHERE sn=?", (sn,))
    conn.commit()
    conn.close()


# ===== 杯贴商品操作 =====

def add_cup_product(name):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO cup_products (name) VALUES (?)", (name.strip(),))
    conn.commit()
    conn.close()


def remove_cup_product(name):
    conn = get_conn()
    conn.execute("DELETE FROM cup_products WHERE name=?", (name,))
    conn.commit()
    conn.close()


def get_cup_products(enabled_only=True):
    conn = get_conn()
    if enabled_only:
        rows = conn.execute("SELECT * FROM cup_products WHERE enabled=1").fetchall()
    else:
        rows = conn.execute("SELECT * FROM cup_products").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_cup_product(name, enabled):
    conn = get_conn()
    conn.execute("UPDATE cup_products SET enabled=? WHERE name=?", (1 if enabled else 0, name))
    conn.commit()
    conn.close()


def is_cup_product(name):
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM cup_products WHERE name=? AND enabled=1", (name,)).fetchone()
    conn.close()
    return row is not None
