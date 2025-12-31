import sqlite3
import hashlib
import os
from config import Config

class Database:
    def __init__(self):
        # تأكد من وجود مجلد database
        db_dir = os.path.dirname(Config.DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        print(f"✅ قاعدة البيانات: {Config.DATABASE_PATH}")
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            phone TEXT,
            balance REAL DEFAULT 0.0,
            total_deposited REAL DEFAULT 0.0,
            total_withdrawn REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول طلبات الإيداع
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            transaction_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # جدول طلبات السحب
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            fee REAL NOT NULL,
            net_amount REAL NOT NULL,
            method TEXT NOT NULL,
            wallet_info TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        self.conn.commit()
    
    # ... باقي الدوال نفسها كما هي ...
    # (ضع باقي دوال database.py التي أرسلتها سابقاً هنا)

db = Database()
