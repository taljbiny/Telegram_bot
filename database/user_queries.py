import psycopg2
from config import DATABASE_URL

def find_or_create_user(user_id, username):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bot_users WHERE telegram_id = %s", (str(user_id),))
        user = cursor.fetchone()
        
        if user:
            cursor.execute("UPDATE bot_users SET last_active = NOW() WHERE id = %s", (user[0],))
            print(f"✅ تم تحديث المستخدم: {user_id}")
        else:
            cursor.execute(
                "INSERT INTO bot_users (telegram_id, user_name, current_state) VALUES (%s, %s, 'start') RETURNING id",
                (str(user_id), username or "No username")
            )
            print(f"✅ تم إنشاء مستخدم جديد: {user_id}")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def save_user_request(user_id, request_type, amount, notes=""):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM bot_users WHERE telegram_id = %s", (str(user_id),))
        result = cursor.fetchone()
        
        if result:
            bot_user_id = result[0]
            cursor.execute(
                "INSERT INTO withdrawal_deposit_requests (bot_user_id, request_type, amount, user_notes) VALUES (%s, %s, %s, %s) RETURNING id",
                (bot_user_id, request_type, amount, notes)
            )
            conn.commit()
            print(f"✅ تم حفظ الطلب: {request_type} - {amount}")
            return True
        return False
    except Exception as e:
        print(f"❌ خطأ في حفظ الطلب: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
