import asyncio
from database.db_connection import create_db_connection

async def test_db():
    print("🔍 جرب الاتصال بقاعدة البيانات...")
    conn = await create_db_connection()
    if conn:
        print("✅ نجح الاتصال!")
        await conn.close()
    else:
        print("❌ فشل الاتصال!")

# تشغيل الاختبار
asyncio.run(test_db())
