import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from datetime import datetime, timezone

from db.base import AsyncSessionLocal
from db.models.user import User
from db.models.kb_entry import KBEntry
from kb.loader import kb_loader

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SAMPLE_KB_DATA = [
    {
        "title": "गेहूं में पीले पत्ते - नाइट्रोजन की कमी",
        "content": "गेहूं की फसल में पीले पत्ते आना नाइट्रोजन की कमी का संकेत है। यह समस्या विशेष रूप से फसल की प्रारंभिक अवस्था में देखी जाती है।",
        "crop_name": "wheat",
        "problem_type": "nutrient_deficiency",
        "solution_steps": "1. यूरिया 50 किलो प्रति एकड़ डालें\n2. पानी दें\n3. 7-10 दिन में सुधार दिखेगा",
        "tags": "wheat,nitrogen,yellow_leaves,fertilizer",
        "language": "hi"
    },
    {
        "title": "धान में भूरा धब्बा रोग",
        "content": "भूरा धब्बा रोग धान की फसल में फंगस के कारण होता है। पत्तियों पर भूरे रंग के धब्बे दिखाई देते हैं।",
        "crop_name": "rice",
        "problem_type": "fungal_disease",
        "solution_steps": "1. कार्बेन्डाजिम स्प्रे करें\n2. खेत में जल निकासी सुधारें\n3. 15 दिन बाद दोबारा स्प्रे करें",
        "tags": "rice,fungal,brown_spot,carbendazim",
        "language": "hi"
    },
    {
        "title": "सोयाबीन में कीट प्रकोप - तना छेदक",
        "content": "तना छेदक कीट सोयाबीन के तने में छेद करके अंदर घुस जाता है। इससे पौधा कमजोर हो जाता है।",
        "crop_name": "soybean",
        "problem_type": "pest_attack",
        "solution_steps": "1. क्लोरपायरीफॉस स्प्रे करें\n2. प्रभावित पौधों को हटा दें\n3. खेत की निगरानी रखें",
        "tags": "soybean,pest,stem_borer,chlorpyrifos",
        "language": "hi"
    },
    {
        "title": "कपास में सिंचाई की समस्या",
        "content": "कपास की फसल को पानी की सही मात्रा चाहिए। कम पानी से पौधे सूख जाते हैं और ज्यादा पानी से जड़ें सड़ सकती हैं।",
        "crop_name": "cotton",
        "problem_type": "irrigation",
        "solution_steps": "1. 10-12 दिन में सिंचाई करें\n2. फूल आने पर नियमित पानी दें\n3. जल निकासी का ध्यान रखें",
        "tags": "cotton,irrigation,water_management",
        "language": "hi"
    },
    {
        "title": "मक्का में खाद प्रबंधन",
        "content": "मक्का की अच्छी पैदावार के लिए संतुलित खाद जरूरी है। एनपीके सही अनुपात में डालना चाहिए।",
        "crop_name": "maize",
        "problem_type": "fertilization",
        "solution_steps": "1. बुवाई के समय DAP 50 किलो\n2. 30 दिन बाद यूरिया 25 किलो\n3. 45 दिन बाद यूरिया 25 किलो",
        "tags": "maize,fertilizer,NPK,urea,DAP",
        "language": "hi"
    }
]

async def seed_data():
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding database...")
        
        # Check if demo user exists
        result = await db.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create demo user
            demo_user = User(
                username="admin",
                email="admin@kisanvani.com",
                hashed_password=pwd_context.hash("admin123"),
                full_name="Admin User",
                role="admin",
                is_active=True
            )
            db.add(demo_user)
            await db.commit()
            print("✅ Demo user created (admin/admin123)")
        else:
            print("ℹ️  Demo user already exists")
        
        # Check if KB entries exist
        kb_result = await db.execute(select(KBEntry))
        existing_kb = kb_result.scalars().all()
        
        if not existing_kb:
            print(f"\n📚 Loading {len(SAMPLE_KB_DATA)} KB entries...")
            
            for kb_data in SAMPLE_KB_DATA:
                kb_entry = KBEntry(
                    **kb_data,
                    is_approved=True,
                    is_banned=False,
                    created_by="system"
                )
                db.add(kb_entry)
            
            await db.commit()
            print(f"✅ Loaded {len(SAMPLE_KB_DATA)} KB entries to MySQL")
            
            # Load to Qdrant if available
            print("\n🔍 Loading entries to vector DB (if Qdrant is available)...")
            kb_result = await db.execute(select(KBEntry))
            all_entries = kb_result.scalars().all()
            
            for entry in all_entries:
                try:
                    await kb_loader.load_entry_to_vector_db(entry)
                    print(f"  ✓ Loaded: {entry.title[:50]}...")
                except Exception as e:
                    print(f"  ⚠ Skipped vector indexing (Qdrant not available): {entry.title[:50]}...")
        else:
            print(f"ℹ️  KB already has {len(existing_kb)} entries")
        
        print("\n✨ Database seeding complete!")
        print("\n🔐 Login credentials:")
        print("   Username: admin")
        print("   Password: admin123")

if __name__ == "__main__":
    asyncio.run(seed_data())
