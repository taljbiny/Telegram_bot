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
            status TEXT DEFAULT 'active',
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
            admin_notes TEXT,
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
            admin_notes TEXT,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # جدول تذاكر الدعم
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            admin_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        self.conn.commit()
    
    # ========== دوال المستخدمين ==========
    
    def user_exists(self, telegram_id):
        """التحقق إذا كان المستخدم موجود"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone() is not None
    
    def username_taken(self, username):
        """التحقق إذا كان اسم المستخدم مستخدم"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
    
    def create_user(self, telegram_id, username, password_hash, phone=None):
        """إنشاء مستخدم جديد"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (telegram_id, username, password_hash, phone)
            VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, password_hash, phone))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, telegram_id):
        """الحصول على بيانات المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        """الحصول على مستخدم بواسطة ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    
    # ========== دوال الرصيد ==========
    
    def update_balance(self, user_id, amount):
        """تحديث رصيد المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET balance = balance + ?, 
            total_deposited = total_deposited + ? 
        WHERE id = ? AND amount > 0
        ''', (amount, amount, user_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def freeze_balance(self, user_id, amount):
        """تجميد جزء من الرصيد"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET balance = balance - ?, 
            frozen_balance = frozen_balance + ? 
        WHERE id = ? AND balance >= ?
        ''', (amount, amount, user_id, amount))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def unfreeze_balance(self, user_id, amount):
        """إلغاء تجميد الرصيد"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET balance = balance + ?, 
            frozen_balance = frozen_balance - ? 
        WHERE id = ? AND frozen_balance >= ?
        ''', (amount, amount, user_id, amount))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def complete_withdrawal(self, user_id, amount):
        """إكمال عملية سحب"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET frozen_balance = frozen_balance - ?, 
            total_withdrawn = total_withdrawn + ? 
        WHERE id = ? AND frozen_balance >= ?
        ''', (amount, amount, user_id, amount))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ========== دوال الإيداع ==========
    
    def create_deposit(self, user_id, amount, method, transaction_id):
        """إنشاء طلب إيداع"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO deposits (user_id, amount, method, transaction_id)
        VALUES (?, ?, ?, ?)
        ''', (user_id, amount, method, transaction_id))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_deposit(self, deposit_id):
        """الحصول على طلب إيداع"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,))
        return cursor.fetchone()
    
    def approve_deposit(self, deposit_id, admin_id):
        """الموافقة على إيداع"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE deposits 
        SET status = 'approved', 
            admin_id = ?, 
            processed_at = CURRENT_TIMESTAMP 
        WHERE id = ? AND status = 'pending'
        ''', (admin_id, deposit_id))
        
        if cursor.rowcount > 0:
            # إضافة الرصيد للمستخدم
            deposit = self.get_deposit(deposit_id)
            self.update_balance(deposit['user_id'], deposit['amount'])
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def reject_deposit(self, deposit_id, admin_id, reason):
        """رفض إيداع"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE deposits 
        SET status = 'rejected', 
            admin_id = ?, 
            admin_notes = ?,
            processed_at = CURRENT_TIMESTAMP 
        WHERE id = ? AND status = 'pending'
        ''', (admin_id, reason, deposit_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_pending_deposits(self):
        """الحصول على طلبات الإيداع المعلقة"""
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
        """إنشاء طلب سحب"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO withdrawals (user_id, amount, fee, net_amount, method, wallet_info)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, fee, net_amount, method, wallet_info))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_withdrawal(self, withdrawal_id):
        """الحصول على طلب سحب"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM withdrawals WHERE id = ?", (withdrawal_id,))
        return cursor.fetchone()
    
    def approve_withdrawal(self, withdrawal_id, admin_id):
        """الموافقة على سحب"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE withdrawals 
        SET status = 'approved', 
            admin_id = ?, 
            processed_at = CURRENT_TIMESTAMP 
        WHERE id = ? AND status = 'pending'
        ''', (admin_id, withdrawal_id))
        
        if cursor.rowcount > 0:
            # إكمال عملية السحب
            withdrawal = self.get_withdrawal(withdrawal_id)
            self.complete_withdrawal(withdrawal['user_id'], withdrawal['amount'])
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def reject_withdrawal(self, withdrawal_id, admin_id, reason):
        """رفض سحب"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE withdrawals 
        SET status = 'rejected', 
            admin_id = ?, 
            admin_notes = ?,
            processed_at = CURRENT_TIMESTAMP 
        WHERE id = ? AND status = 'pending'
        ''', (admin_id, reason, withdrawal_id))
        
        if cursor.rowcount > 0:
            # إرجاع المبلغ المجمد
            withdrawal = self.get_withdrawal(withdrawal_id)
            self.unfreeze_balance(withdrawal['user_id'], withdrawal['amount'])
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_pending_withdrawals(self):
        """الحصول على طلبات السحب المعلقة"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT w.*, u.username, u.telegram_id 
        FROM withdrawals w
        JOIN users u ON w.user_id = u.id
        WHERE w.status = 'pending'
        ORDER BY w.created_at DESC
        ''')
        return cursor.fetchall()
    
    # ========== دوال الدعم ==========
    
    def create_support_ticket(self, user_id, message):
        """إنشاء تذكرة دعم"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO support_tickets (user_id, message)
        VALUES (?, ?)
        ''', (user_id, message))
        self.conn.commit()
        return cursor.lastrowid
    
    def reply_to_ticket(self, ticket_id, reply):
        """الرد على تذكرة دعم"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE support_tickets 
        SET status = 'closed', 
            admin_reply = ? 
        WHERE id = ?
        ''', (reply, ticket_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_open_tickets(self):
        """الحصول على تذاكر الدعم المفتوحة"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT s.*, u.username, u.telegram_id 
        FROM support_tickets s
        JOIN users u ON s.user_id = u.id
        WHERE s.status = 'open'
        ORDER BY s.created_at DESC
        ''')
        return cursor.fetchall()
    
    # ========== دوال الإحصائيات ==========
    
    def get_stats(self):
        """الحصول على إحصائيات النظام"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # إحصائيات المستخدمين
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')")
        stats['new_today'] = cursor.fetchone()[0]
        
        # إحصائيات مالية
        cursor.execute("SELECT SUM(balance) FROM users")
        stats['total_balance'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(frozen_balance) FROM users")
        stats['frozen_balance'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM deposits WHERE status = 'approved' AND DATE(created_at) = DATE('now')")
        stats['deposits_today'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(net_amount) FROM withdrawals WHERE status = 'approved' AND DATE(created_at) = DATE('now')")
        stats['withdrawals_today'] = cursor.fetchone()[0] or 0
        
        # الطلبات المعلقة
        cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'pending'")
        stats['pending_deposits'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'pending'")
        stats['pending_withdrawals'] = cursor.fetchone()[0]
        
        return stats

# إنشاء كائن قاعدة البيانات
db = Database()
