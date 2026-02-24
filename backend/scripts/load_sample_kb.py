import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from db.base import AsyncSessionLocal
from db.models.kb_entry import KBEntry
from kb.loader import kb_loader

SAMPLE_KB_DATA = [
    {
        "title": "गेहूं में पीले पत्ते - नाइट्रोजन की कमी",
        "content": "गेहूं की फसल में पीले पत्ते आना नाइट्रोजन की कमी का संकेत है। यह समस्या विशेष रूप से फसल की प्रारंभिक अवस्था में देखी जाती है। पुराने पत्ते पहले पीले होते हैं।",
        "crop_name": "wheat",
        "problem_type": "nutrient_deficiency",
        "solution_steps": "1. यूरिया 50 किलो प्रति एकड़ डालें\n2. पानी दें\n3. 7-10 दिन में सुधार दिखेगा",
        "tags": "wheat,nitrogen,yellow_leaves,fertilizer",
        "language": "hi"
    },
    {
        "title": "धान में भूरा धब्बा रोग",
        "content": "भूरा धब्बा रोग धान की फसल में फंगस के कारण होता है। पत्तियों पर भूरे रंग के धब्बे दिखाई देते हैं। यह रोग नमी और गर्म मौसम में तेजी से फैलता है।",
        "crop_name": "rice",
        "problem_type": "fungal_disease",
        "solution_steps": "1. कार्बेन्डाजिम स्प्रे करें\n2. खेत में जल निकासी सुधारें\n3. 15 दिन बाद दोबारा स्प्रे करें",
        "tags": "rice,fungal,brown_spot,carbendazim",
        "language": "hi"
    },
    {
        "title": "सोयाबीन में कीट प्रकोप - तना छेदक",
        "content": "तना छेदक कीट सोयाबीन के तने में छेद करके अंदर घुस जाता है। इससे पौधा कमजोर हो जाता है और उपज कम हो जाती है। पौधे का ऊपरी हिस्सा मुरझा सकता है।",
        "crop_name": "soybean",
        "problem_type": "pest_attack",
        "solution_steps": "1. क्लोरपायरीफॉस स्प्रे करें\n2. प्रभावित पौधों को हटा दें\n3. खेत की निगरानी रखें",
        "tags": "soybean,pest,stem_borer,chlorpyrifos",
        "language": "hi"
    },
    {
        "title": "कपास में सिंचाई की समस्या",
        "content": "कपास की फसल को पानी की सही मात्रा चाहिए। कम पानी से पौधे सूख जाते हैं और ज्यादा पानी से जड़ें सड़ सकती हैं। फूल आने के समय पर्याप्त पानी जरूरी है।",
        "crop_name": "cotton",
        "problem_type": "irrigation",
        "solution_steps": "1. 10-12 दिन में सिंचाई करें\n2. फूल आने पर नियमित पानी दें\n3. जल निकासी का ध्यान रखें",
        "tags": "cotton,irrigation,water_management",
        "language": "hi"
    },
    {
        "title": "मक्का में खाद प्रबंधन",
        "content": "मक्का की अच्छी पैदावार के लिए संतुलित खाद जरूरी है। एनपीके (नाइट्रोजन, फॉस्फोरस, पोटैशियम) सही अनुपात में डालना चाहिए।",
        "crop_name": "maize",
        "problem_type": "fertilization",
        "solution_steps": "1. बुवाई के समय DAP 50 किलो\n2. 30 दिन बाद यूरिया 25 किलो\n3. 45 दिन बाद यूरिया 25 किलो",
        "tags": "maize,fertilizer,NPK,urea,DAP",
        "language": "hi"
    }
]

async def load_sample_data():
    async with AsyncSessionLocal() as db:
        print("Loading sample KB entries...")
        
        for kb_data in SAMPLE_KB_DATA:
            kb_entry = KBEntry(
                **kb_data,
                is_approved=True,
                is_banned=False,
                created_by="system"
            )
            db.add(kb_entry)
        
        await db.commit()
        
        print(f"Loaded {len(SAMPLE_KB_DATA)} KB entries to MySQL")
        
        result = await db.execute("SELECT id, title FROM kb_entries")
        entries = result.fetchall()
        
        print("\nLoading to Qdrant vector DB...")
        for entry_id, title in entries:
            result = await db.execute(f"SELECT * FROM kb_entries WHERE id = {entry_id}")
            entry = result.fetchone()
            if entry:
                kb_entry = KBEntry(
                    id=entry[0],
                    title=entry[1],
                    content=entry[2],
                    crop_name=entry[3],
                    problem_type=entry[4],
                    solution_steps=entry[5],
                    tags=entry[6],
                    is_approved=entry[7],
                    is_banned=entry[8],
                    language=entry[9]
                )
                await kb_loader.load_entry_to_vector_db(kb_entry)
                print(f"  - Loaded: {title}")
        
        print("\n✅ Sample KB data loaded successfully!")

if __name__ == "__main__":
    asyncio.run(load_sample_data())
