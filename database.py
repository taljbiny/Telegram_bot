cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT NOT NULL UNIQUE,  -- اسم المستخدم الجديد
    password_hash TEXT NOT NULL,    -- كلمة السر المشفرة
    phone_number TEXT,              -- اختياري
    balance REAL DEFAULT 0.0,
    total_deposited REAL DEFAULT 0.0,
    total_withdrawn REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',   -- مباشرة active بدون موافقة
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
