import sqlite3
import hashlib
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT NOT NULL,
            phone_number TEXT UNIQUE,
            balance REAL DEFAULT 0.0,
            total_deposited REAL DEFAULT 0.0,
            total_withdrawn REAL DEFAULT 0.0,
            referral_code TEXT UNIQUE,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول طلبات الإيداع
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            receipt_image TEXT,
            status TEXT DEFAULT 'pending',  -- pending, approved, rejected
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
        ''')
        
        # جدول طلبات السحب
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            net_amount REAL NOT NULL,
            fee REAL NOT NULL,
            wallet_address TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT DEFAULT 'pending',  -- pending, processing, completed, rejected
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
        ''')
        
        # جدول محادثات الدعم
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'open',  -- open, closed
            admin_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
        ''')
        
        self.conn.commit()
    
    # ... باقي الدوال (سأكملها في الملف الكامل)
    
    def add_support_ticket(self, user_id, message):
        """إضافة تذكرة دعم جديدة"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO support_tickets (user_id, message) VALUES (?, ?)",
            (user_id, message)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_deposits(self):
        """الحصول على طلبات الإيداع المعلقة"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM deposit_requests WHERE status = 'pending' ORDER BY created_at DESC"
        )
        return cursor.fetchall()
    
    def get_pending_withdrawals(self):
        """الحصول على طلبات السحب المعلقة"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM withdrawal_requests WHERE status = 'pending' ORDER BY created_at DESC"
        )
        return cursor.fetchall()

db = Database()
