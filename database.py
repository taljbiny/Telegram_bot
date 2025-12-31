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
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            phone TEXT,
            balance REAL DEFAULT 0.0,
            total_deposited REAL DEFAULT 0.0,
            total_withdrawn REAL DEFAULT 0.0,
            frozen_balance REAL DEFAULT 0.0,
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
    
    # ========== دوال المستخدمين ==========
    
    def user_exists(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone() is not None
    
    def username_taken(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
    
    def create_user(self, telegram_id, username, password_hash, phone=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (telegram_id, username, password_hash, phone)
            VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, password_hash, phone))
            self.conn.commit()
            return True
        except:
            return False
    
    def get_user(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone()
    
    def update_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET balance = balance + ?, 
            total_deposited = total_deposited + ? 
        WHERE id = ? AND amount > 0
        ''', (amount, amount, user_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ========== دوال الإيداع ==========
    
    def create_deposit(self, user_id, amount, method, transaction_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO deposits (user_id, amount, method, transaction_id)
        VALUES (?, ?, ?, ?)
        ''', (user_id, amount, method, transaction_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_deposit(self, deposit_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,))
        return cursor.fetchone()
    
    def approve_deposit(self, deposit_id, admin_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE deposits 
        SET status = 'approved', 
            admin_id = ?, 
            processed_at = CURRENT_TIMESTAMP 
        WHERE id = ? AND status = 'pending'
        ''', (admin_id, deposit_id))
        
        if cursor.rowcount > 0:
            deposit = self.get_deposit(deposit_id)
            self.update_balance(deposit['user_id'], deposit['amount'])
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_pending_deposits(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT d.*, u.username, u.telegram_id 
        FROM deposits d
        JOIN users u ON d.user_id = u.id
        WHERE d.status = 'pending'
        ORDER BY d.created_at DESC
        ''')
        return cursor.fetchall()
    
    # ========== دوال السحب ==========
    
    def create_withdrawal(self, user_id, amount, fee, net_amount, method, wallet_info):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO withdrawals (user_id, amount, fee, net_amount, method, wallet_info)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, fee, net_amount, method, wallet_info))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_withdrawal(self, withdrawal_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM withdrawals WHERE id = ?", (withdrawal_id,))
        return cursor.fetchone()
    
    def approve_withdrawal(self, withdrawal_id, admin_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE withdrawals 
        SET status = 'approved', 
            admin_id = ?, 
            processed_at = CURRENT_TIMESTAMP 
        WHERE id = ? AND status = 'pending'
        ''', (admin_id, withdrawal_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_pending_withdrawals(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT w.*, u.username, u.telegram_id 
        FROM withdrawals w
        JOIN users u ON w.user_id = u.id
        WHERE w.status = 'pending'
        ORDER BY w.created_at DESC
        ''')
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()

db = Database()
