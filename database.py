import sqlite3

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        account_name TEXT,
        password TEXT,
        balance REAL DEFAULT 0,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        amount REAL,
        method TEXT,
        proof TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        amount REAL,
        fee REAL,
        net REAL,
        wallet_type TEXT,
        wallet_number TEXT,
        status TEXT
    )
    """)

    conn.commit()
    return conn, cur
