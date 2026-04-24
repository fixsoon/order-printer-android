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

    c.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_default INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ingredient_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            storage_type TEXT DEFAULT '常温',
            valid_hours INTEGER DEFAULT 24,
            category TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS food_sample_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            default_weight TEXT DEFAULT '150g'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    """)
    default_cats = ["鲜切水果", "茶饮小料", "现萃茶底", "粉类", "果酱/果汁", "牛奶"]
    for i, name in enumerate(default_cats):
        c.execute("INSERT OR IGNORE INTO categories (name, sort_order) VALUES (?, ?)", (name, i))

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


# ===== 兼容层（适配新版 UI） =====

def get_all_printers():
    """返回所有打印机，不分类"""
    return get_printers(purpose=None)


def save_printer(data):
    """保存打印机，data 包含 sn/name/key/type/is_default"""
    return add_printer(
        sn=data.get('sn', ''),
        key=data.get('key', ''),
        name=data.get('name', ''),
        purpose=data.get('type', data.get('purpose', 'receipt')),
        is_default=data.get('is_default', False)
    )


def delete_printer_by_id(printer_id):
    """按 ID 删除打印机"""
    conn = get_conn()
    conn.execute("DELETE FROM printers WHERE id=?", (printer_id,))
    conn.commit()
    conn.close()


# ===== 经手人管理 =====

def init_operators():
    """初始化经手人表"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            is_default INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_operator(name):
    """添加经手人"""
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO operators (name) VALUES (?)", (name.strip(),))
    conn.commit()
    conn.close()


def remove_operator(name):
    conn = get_conn()
    conn.execute("DELETE FROM operators WHERE name=?", (name,))
    conn.commit()
    conn.close()


def get_operators():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM operators").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_default_operator(name):
    conn = get_conn()
    conn.execute("UPDATE operators SET is_default=0")
    conn.execute("UPDATE operators SET is_default=1 WHERE name=?", (name,))
    conn.commit()
    conn.close()


def get_default_operator():
    conn = get_conn()
    row = conn.execute("SELECT * FROM operators WHERE is_default=1 LIMIT 1").fetchone()
    if row:
        result = dict(row)
        conn.close()
        return result
    row = conn.execute("SELECT * FROM operators LIMIT 1").fetchone()
    result = dict(row) if row else None
    conn.close()
    return result


# ===== 食材期效模板 =====

def init_ingredient_templates():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ingredient_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            storage_type TEXT DEFAULT '常温',
            valid_hours INTEGER DEFAULT 24,
            category TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


def add_ingredient_template(name, storage_type='常温', valid_hours=24, category=''):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO ingredient_templates (name, storage_type, valid_hours, category) VALUES (?,?,?,?)",
        (name.strip(), storage_type, int(valid_hours), category.strip())
    )
    conn.commit()
    conn.close()


def remove_ingredient_template(name):
    conn = get_conn()
    conn.execute("DELETE FROM ingredient_templates WHERE name=?", (name,))
    conn.commit()
    conn.close()


# ===== 品类分类管理 =====

def init_categories():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    """)
    # 初始化默认分类
    default_cats = ["鲜切水果", "茶饮小料", "现萃茶底", "粉类", "果酱/果汁", "牛奶"]
    for i, name in enumerate(default_cats):
        conn.execute("INSERT OR IGNORE INTO categories (name, sort_order) VALUES (?, ?)", (name, i))
    conn.commit()
    conn.close()


def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_category(name):
    conn = get_conn()
    max_order = conn.execute("SELECT MAX(sort_order) FROM categories").fetchone()[0] or 0
    conn.execute("INSERT OR IGNORE INTO categories (name, sort_order) VALUES (?, ?)", (name.strip(), max_order + 1))
    conn.commit()
    conn.close()


def remove_category(name):
    conn = get_conn()
    conn.execute("DELETE FROM categories WHERE name=?", (name,))
    conn.commit()
    conn.close()


def update_template_category(template_name, category):
    conn = get_conn()
    conn.execute("UPDATE ingredient_templates SET category=? WHERE name=?", (category, template_name))
    conn.commit()
    conn.close()


def get_templates_by_category(category):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM ingredient_templates WHERE category=?", (category,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ingredient_templates():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM ingredient_templates ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===== 食品留样模板 =====

def init_food_sample_templates():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS food_sample_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            default_weight TEXT DEFAULT '150g'
        )
    """)
    conn.commit()
    conn.close()


def add_food_sample_template(name, default_weight='150g'):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO food_sample_templates (name, default_weight) VALUES (?,?)",
        (name.strip(), default_weight)
    )
    conn.commit()
    conn.close()


def remove_food_sample_template(name):
    conn = get_conn()
    conn.execute("DELETE FROM food_sample_templates WHERE name=?", (name,))
    conn.commit()
    conn.close()


def get_food_sample_templates():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM food_sample_templates").fetchall()
    conn.close()
    return [dict(r) for r in rows]
