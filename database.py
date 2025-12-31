# تحديث إنشاء الجدول
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    phone_number TEXT UNIQUE,
    email TEXT,
    country TEXT,
    id_card_image TEXT,  # صورة الهوية
    selfie_image TEXT,   # صورة سيلفي مع الهوية
    balance REAL DEFAULT 0.0,
    total_deposited REAL DEFAULT 0.0,
    total_withdrawn REAL DEFAULT 0.0,
    status TEXT DEFAULT 'pending',  -- pending, active, rejected, suspended
    rejection_reason TEXT,
    verified_by INTEGER,  -- ID المشرف الذي وافق
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
