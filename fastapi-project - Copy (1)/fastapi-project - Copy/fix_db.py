import sqlite3

# تأكدي إنك في نفس الفولدر اللي فيه الملف
conn = sqlite3.connect('food_donation.db')
cursor = conn.cursor()

# 1. تنظيف أي طلبات قديمة كانت عاملة زحمة
cursor.execute("DELETE FROM requests") 

# 2. تعديل الحالة لـ APPROVED (بالحروف الكبيرة) ✅
cursor.execute("UPDATE donations SET status = 'APPROVED'")

conn.commit()
conn.close()

print("✅ الداتابيز اتنظفت والوجبات بقت جاهزة يا منة!")