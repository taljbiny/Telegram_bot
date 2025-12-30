import sqlite3

def init_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    cur = conn.cursor()

    # جدول المستخدمين
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        account_name TEXT,
        password TEXT,
        balance INTEGER DEFAULT 0
    )
    """)

    # جدول الإيداعات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        amount INTEGER,
        method TEXT,
        proof TEXT,
        status TEXT
    )
    """)

    # جدول السحوبات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        amount INTEGER,
        fee INTEGER,
        net INTEGER,
        wallet_type TEXT,
        wallet_number TEXT,
        status TEXT
    )
    """)

    # سجل كامل لكل العمليات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        action TEXT,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    return conn, cur
