import sys, os
import random
from faker import Faker
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.session import SessionLocal, engine
from db.base import Base
import models
from core.security import hash_password
from models.user import User, UserRole
from models.donation import Donation, DonationStatus
from models.request import Request, RequestStatus
from models.delivery import DeliveryAssignment, DeliveryStatus
from models.audit_log import AuditLog
from models.notification import Notification, NotificationType 

fake = Faker(['ar_EG'])

def seed():
    print("🗑️ [1/4] جاري تنظيف الجداول تماماً لتهيئة السكيل المليوني المتنوع...")
    Base.metadata.drop_all(bind=engine) 
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()

    try:
        print("⏳ [2/4] جاري تشفير الباسوردات القياسية...")
        hashed_admin = hash_password("Admin1234")
        hashed_volunteer = hash_password("Volunteer1234")
        hashed_donor = hash_password("Donor1234")
        hashed_charity = hash_password("Charity1234")

        admin = User(
            name="مدير النظام العام", email="admin@fooddonation.com",
            hashed_password=hashed_admin, role=UserRole.ADMIN,
            phone_number="+201000000001", address="القاهرة، مصر"
        )
        volunteer_main = User(
            name="أحمد مصطفى (متطوع)", email="ahmed.vol@gmail.com",
            hashed_password=hashed_volunteer, role=UserRole.VOLUNTEER,
            phone_number="+201000000006", address="الدقي، الجيزة"
        )
        hotel_main = User(
            name="فندق ريتز كارلتون", email="hotel@gmail.com",
            hashed_password=hashed_donor, role=UserRole.DONOR,
            phone_number="+201000000007", address="وسط البلد، القاهرة"
        )
        charity_main = User(
            name="جمعية الأمل الخيرية", email="charity@gmail.com",
            hashed_password=hashed_charity, role=UserRole.CHARITY,
            phone_number="+201000000008", address="مدينة نصر، القاهرة"
        )

        db.add_all([admin, volunteer_main, hotel_main, charity_main])
        db.flush()

        donors = [hotel_main]
        charities = [charity_main]
        volunteers = [volunteer_main]

        for i in range(1500):  
            donors.append(User(
                name=f"شركة التبرع الفندقية رقم {i}", email=f"donor_bulk_{i}@food.com",
                hashed_password=hashed_donor, role=UserRole.DONOR,
                phone_number=f"+2012{random.randint(10000000, 99999999)}", address=fake.address()
            ))
            
        for i in range(800):  
            charities.append(User(
                name=f"جمعية الرعاية والخير فرع {i}", email=f"charity_bulk_{i}@charity.com",
                hashed_password=hashed_charity, role=UserRole.CHARITY,
                phone_number=f"+2011{random.randint(10000000, 99999999)}", address=fake.address()
            ))

        for i in range(1200):  
            volunteers.append(User(
                name=f"كابتن متطوع رقم {i}", email=f"volunteer_bulk_{i}@vol.com",
                hashed_password=hashed_volunteer, role=UserRole.VOLUNTEER,
                phone_number=f"+2010{random.randint(10000000, 99999999)}", address=fake.address()
            ))

        db.bulk_save_objects(donors[1:] + charities[1:] + volunteers[1:])
        db.commit()
        
        db_donors = db.query(User).filter(User.role == UserRole.DONOR).all()
        db_charities = db.query(User).filter(User.role == UserRole.CHARITY).all()
        db_volunteers = db.query(User).filter(User.role == UserRole.VOLUNTEER).all()

        print("🍕 [3/4] جاري ضخ التبرعات بروابط صور مختلفة تماماً 📸...")
        food_items = ["وجبات أرز ودجاج طازجة", "بيتزا مشكلة عائلية", "ساندوتشات لحم برجر وفرايز", "وجبات لحوم وخضار ساخنة", "كراتين مواد غذائية جافة"]
        food_types = ["وجبات مطبوخة", "مواد خام وجافة", "فواكه وخضروات", "مخبوزات وحلويات", "تبرع غذائي مشكل"]
        expiry_options = ["3 ساعات", "6 ساعات", "12 ساعة", "24 ساعة"]
        
        # 🔥 تم تغيير روابط الصور بروابط مباشرة لـ 5 أكلات مختلفة تماماً لضمان عدم التكرار
        food_images = [
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=500", # سلطة صحية
            "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=500", # بيتزا واضحة
            "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=500", # برجر وفرايز
            "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=500", # وجبة لحوم مشوية
            "https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=500"  # وجبة طعام متنوعة
        ]
        
        TOTAL_DONATIONS = 50000
        BATCH_SIZE = 5000
        
        for batch_start in range(0, TOTAL_DONATIONS, BATCH_SIZE):
            batch_donations = []
            for _ in range(BATCH_SIZE):
                # نختار لفة الصورة بناءً على نوع الوجبة ليكون هناك تناسق مبهر
                chosen_title = random.choice(food_items)
                img_index = food_items.index(chosen_title)
                
                batch_donations.append(Donation(
                    title=chosen_title,
                    description="وجبات غذائية صالحة ومغلفة ومعدة للتوزيع الفوري لبيئة الاختبار وضمان الكفاءة.",
                    food_type=random.choice(food_types),
                    quantity=random.randint(10, 500),
                    status=random.choice(list(DonationStatus)),
                    donor_id=random.choice(db_donors).id,
                    photo_url=food_images[img_index], # 👈 ربط الصورة بنوع الأكلة عشان التنوع
                    approved_by=admin.id if random.random() > 0.2 else None,
                    date_created=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 90)),
                    expiry_time=random.choice(expiry_options)
                ))
            db.bulk_save_objects(batch_donations)
            db.commit()

        all_saved_donations = db.query(Donation).all()
        print("⚙️ [4/4] جاري غزل السلسلة الزمنية المتكاملة للإشعارات المتبادلة 🔄...")

        bulk_requests = []
        bulk_assignments = []
        bulk_notifications = []
        
        counter = 0
        for donation in all_saved_donations:
            otp_code = str(random.randint(1000, 9999))
            
            # 🏢 خطوة 1 ثابتة لجميع التبرعات: إشعار للفندق إن تبرعه اتوافق عليه من الإدارة
            bulk_notifications.append(Notification(
                user_id=donation.donor_id, donation_id=donation.id,
                title="تمت الموافقة على التبرع ✅", 
                message=f"تمت مراجعة تبرعك بـ ({donation.title}) وهو متاح حالياً للجمعيات.",
                notification_type=NotificationType.DONATION_UPDATE, is_interactive=False,
                created_at=donation.date_created
            ))

            # اختيار عشوائي ذكي ومثبت للجمعية والمتطوع لربط أطراف السيناريو
            chosen_charity = charity_main if random.random() > 0.4 else random.choice(db_charities)
            chosen_volunteer = volunteer_main if random.random() > 0.4 else random.choice(db_volunteers)

            # 🔄 [السيناريو الأول]: طلبات لسه "في الطريق" أو "مقبولة حديثاً"
            if donation.status in [DonationStatus.APPROVED, DonationStatus.PENDING]:
                
                # 1. إشعار يروح للفندق (المتبرع): الجمعية طلبت تبرعك حالاً!
                bulk_notifications.append(Notification(
                    user_id=donation.donor_id, donation_id=donation.id,
                    title="طلب جديد على تبرعك 🔔",
                    message=f"قامت ({chosen_charity.name}) بطلب وجبات ({donation.title}). يرجى تأكيد التحضير للمندوب.",
                    notification_type=NotificationType.DONATION_UPDATE, is_interactive=False,
                    created_at=donation.date_created + timedelta(minutes=10)
                ))
                
                # 2. إشعار يروح للجمعية: تم قبول طلبك وجاري التنسيق
                bulk_notifications.append(Notification(
                    user_id=chosen_charity.id, donation_id=donation.id,
                    title="تم قبول الطلب ✅",
                    message=f"تمت الموافقة على طلبكم لاستلام ({donation.title}). جاري تعيين متطوع قريب.",
                    notification_type=NotificationType.REQUEST_UPDATE, location=chosen_charity.address,
                    is_interactive=False, created_at=donation.date_created + timedelta(minutes=15)
                ))

                # 3. إشعار يروح للجمعية: المتطوع استلم الأكل وهو في الطريق إليكم
                if donation.status == DonationStatus.APPROVED:
                    bulk_notifications.append(Notification(
                        user_id=chosen_charity.id, donation_id=donation.id,
                        title="الطلب في الطريق إليكم 🚚", 
                        message=f"انطلق المندوب {chosen_volunteer.name} بـ ({donation.title}) الآن ومتحرك نحو مقركم.",
                        notification_type=NotificationType.REQUEST_UPDATE, location=chosen_charity.address,
                        is_interactive=True, created_at=donation.date_created + timedelta(minutes=30)
                    ))

            # 🔄 [السيناريو الثاني المكتمل]: طلبات تم تسليمها بنجاح واكتملت دورتها بالكامل
            elif donation.status == DonationStatus.DELIVERED:
                
                # ربط السجلات الجانبية لضمان حساب الإحصائيات الحية بشكل سليم
                bulk_requests.append(Request(
                    donation_id=donation.id, charity_id=chosen_charity.id,
                    food_type=donation.food_type, quantity=donation.quantity, status=RequestStatus.ACCEPTED,
                    notes=f"تم تسليم {donation.title} بنجاح."
                ))
                
                bulk_assignments.append(DeliveryAssignment(
                    donation_id=donation.id, volunteer_id=chosen_volunteer.id, assigned_by=admin.id,
                    status=DeliveryStatus.DELIVERED, security_code=otp_code
                ))

                # ⏳ غزل السلسلة التاريخية للطلب المكتمل خطوة بخطوة بالترتيب الزمني:
                
                # 1. إشعار للفندق: الجمعية طلبت الأكل
                bulk_notifications.append(Notification(
                    user_id=donation.donor_id, donation_id=donation.id,
                    title="طلب جديد على تبرعك 🔔",
                    message=f"قامت ({chosen_charity.name}) بطلب وجبات ({donation.title}).",
                    notification_type=NotificationType.DONATION_UPDATE, is_interactive=False,
                    created_at=donation.date_created + timedelta(minutes=10)
                ))
                
                # 2. إشعار للجمعية: الطلب اتوافق عليه
                bulk_notifications.append(Notification(
                    user_id=chosen_charity.id, donation_id=donation.id,
                    title="تم قبول الطلب ✅",
                    message=f"تمت الموافقة على طلبكم لـ ({donation.title}).",
                    notification_type=NotificationType.REQUEST_UPDATE, location=chosen_charity.address,
                    is_interactive=False, created_at=donation.date_created + timedelta(minutes=15)
                ))
                
                # 3. إشعار للجمعية: الطلب في الطريق
                bulk_notifications.append(Notification(
                    user_id=chosen_charity.id, donation_id=donation.id,
                    title="الطلب في الطريق إليكم 🚚", 
                    message=f"انطلق المندوب {chosen_volunteer.name} بـ ({donation.title}) ومتحرك نحو مقركم.",
                    notification_type=NotificationType.REQUEST_UPDATE, location=chosen_charity.address,
                    is_interactive=False, created_at=donation.date_created + timedelta(minutes=30)
                ))
                
                # 4. إشعار للجمعية: تم التسليم بنجاح (لفتح التقييم الفوري)
                bulk_notifications.append(Notification(
                    user_id=chosen_charity.id, donation_id=donation.id,
                    title="تم تسليم الطلب بنجاح 🎉", 
                    message=f"قام المتطوع بتسليم وجبات ({donation.title}) لمقرك الآن بنجاح. اضغط للتقييم.",
                    notification_type=NotificationType.REQUEST_UPDATE, location=chosen_charity.address,
                    is_interactive=True, created_at=donation.date_created + timedelta(hours=1)
                ))
                
                # 5. إشعار للفندق: تبرعك وصل بالسلامة والجمعية استلمته
                bulk_notifications.append(Notification(
                    user_id=donation.donor_id, donation_id=donation.id,
                    title="تم اكتمال التوصيل بنجاح 🌟",
                    message=f"تم تسليم تبرعك بـ ({donation.title}) إلى ({chosen_charity.name}) بنجاح. شكراً لعطائك العظيم!",
                    notification_type=NotificationType.DONATION_UPDATE, is_interactive=False,
                    created_at=donation.date_created + timedelta(hours=1, minutes=5)
                ))

            counter += 1
            if counter % 5000 == 0:
                db.bulk_save_objects(bulk_requests)
                db.bulk_save_objects(bulk_assignments)
                db.bulk_save_objects(bulk_notifications)
                db.commit()
                bulk_requests.clear()
                bulk_assignments.clear()
                bulk_notifications.clear()

        if bulk_requests or bulk_assignments or bulk_notifications:
            db.bulk_save_objects(bulk_requests)
            db.bulk_save_objects(bulk_assignments)
            db.bulk_save_objects(bulk_notifications)
            db.commit()

        print("\n🏆 تم ضبط وإغلاق السيناريوهات المتداخلة والمتبادلة بنجاح 100%!")

    except Exception as e:
        db.rollback()
        print(f"❌ خطأ أثناء زراعة الإشعارات: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()