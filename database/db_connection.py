import psycopg2
from config import DATABASE_URL

def create_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
        return conn
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return None

def test_connection():
    """دالة اختبار الاتصال"""
    conn = create_db_connection()
    if conn:
        print("🎉 الاتصال ناجح!")
        conn.close()
        return True
    else:
        print("💥 الاتصال فاشل!")
        return False
