"""
Populate kb_entries table with wheat-related knowledge
Also indexes them in Qdrant vector database
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models.kb_entry import KBEntry
from core.config import settings
from datetime import datetime, timezone

# Knowledge base entries for wheat
WHEAT_KB_ENTRIES = [
    {
        "title": "गेहूं में पीले पत्ते - नाइट्रोजन की कमी",
        "content": "गेहूं में पीले पत्ते नाइट्रोजन की कमी के मुख्य लक्षण हैं। पुरानी पत्तियां पहले पीली होती हैं फिर धीरे-धीरे पूरा पौधा पीला पड़ जाता है। पौधे की वृद्धि रुक जाती है और कल्ले कम फूटते हैं।\n\nतुरंत उपचार: यूरिया खाद 100 किलो प्रति एकड़ तुरंत डालें। पहली सिंचाई के साथ 50 किलो और दूसरी सिंचाई के साथ 50 किलो डालें। यूरिया को पानी में घोलकर स्प्रे भी कर सकते हैं (2% घोल)।\n\nलंबे समय का समाधान: मिट्टी की जांच कराएं। जैविक खाद (गोबर की खाद) 5-7 टन प्रति एकड़ हर साल डालें। हरी खाद की फसल लगाएं। संतुलित उर्वरक NPK का प्रयोग करें।",
        "crop_name": "wheat",
        "problem_type": "nutrient_deficiency",
        "solution_steps": "1. यूरिया 100 किलो/एकड़ तुरंत डालें\n2. दो भागों में डालें - पहली और दूसरी सिंचाई के साथ\n3. मिट्टी परीक्षण कराएं\n4. जैविक खाद का प्रयोग बढ़ाएं",
        "tags": "पीले पत्ते,नाइट्रोजन,यूरिया,पोषक तत्व,yellow leaves,nitrogen",
        "language": "hi"
    },
    {
        "title": "गेहूं में रतुआ रोग - पीला, भूरा, काला",
        "content": "गेहूं में रतुआ तीन प्रकार का होता है:\n1. पीला रतुआ: पत्तियों पर पीले रंग के पाउडर जैसे धब्बे, ठंडे मौसम में ज्यादा\n2. भूरा रतुआ: पत्तियों पर भूरे-नारंगी रंग के धब्बे, गर्म मौसम में\n3. काला रतुआ: तने और पत्तियों पर काले धब्बे, सबसे खतरनाक\n\nलक्षण: पत्तियों पर धब्बे जो हाथ लगाने से पाउडर की तरह निकलते हैं। पौधा कमजोर होता है, दाना कम भरता है।\n\nउपचार: प्रोपिकोनाजोल 25% EC 1 मिली/लीटर या टेबुकोनाजोल 1 मिली/लीटर पानी में मिलाकर छिड़काव करें। 15 दिन बाद दोबारा स्प्रे करें। रोग की शुरुआत में ही उपचार जरूरी है।\n\nरोकथाम: रोग प्रतिरोधी किस्में लगाएं (HD-2967, WH-1105, DBW-88)। संतुलित खाद डालें। खेत में जल निकासी अच्छी रखें। बीज उपचार जरूर करें।",
        "crop_name": "wheat",
        "problem_type": "disease",
        "solution_steps": "1. प्रोपिकोनाजोल 1 मिली/लीटर छिड़काव\n2. 15 दिन बाद दोबारा स्प्रे\n3. रोग प्रतिरोधी किस्में उगाएं\n4. संतुलित खाद और अच्छी जल निकासी",
        "tags": "रतुआ,rust,पीला रतुआ,भूरा रतुआ,काला रतुआ,fungicide,propiconazole",
        "language": "hi"
    },
    {
        "title": "गेहूं की देरी से बुवाई - किस्म और प्रबंधन",
        "content": "दिसंबर में देरी से बुवाई करने पर उपज कम हो जाती है क्योंकि फसल को कम समय मिलता है। सही किस्म और प्रबंधन से नुकसान कम किया जा सकता है।\n\nशीघ्र पकने वाली किस्में:\n• DBW-187: 110 दिन में पक जाती है, गर्मी सहनशील\n• HD-3086: 115 दिन, उच्च उपज देने वाली\n• PBW-725: 120 दिन, देरी से बुवाई के लिए उत्तम\n• PBW-590, DBW-17 भी अच्छी हैं\n\nप्रबंधन:\n• बीज दर 25% बढ़ाएं (125-130 किलो/हेक्टेयर)\n• पहली सिंचाई 15-20 दिन में दें (जल्दी)\n• यूरिया की पूरी मात्रा 2 बार में डालें (20 और 40 दिन पर)\n• गर्मी से बचाव के लिए आखिरी सिंचाई दाना भरते समय जरूर दें\n• खरपतवार नियंत्रण जल्दी करें",
        "crop_name": "wheat",
        "problem_type": "late_sowing",
        "solution_steps": "1. शीघ्र पकने वाली किस्में चुनें (DBW-187, HD-3086)\n2. बीज दर 25% बढ़ाएं\n3. पहली सिंचाई 15-20 दिन में\n4. यूरिया 2 बार में डालें\n5. आखिरी सिंचाई जरूर दें",
        "tags": "देरी से बुवाई,late sowing,variety,किस्म,DBW-187,HD-3086,PBW-725",
        "language": "hi"
    },
    {
        "title": "गेहूं में माहू (Aphid) कीट नियंत्रण",
        "content": "माहू गेहूं का प्रमुख कीट है जो पत्तियों और बालियों से रस चूसता है। फरवरी-मार्च में सबसे ज्यादा नुकसान करता है।\n\nपहचान: छोटे हरे/काले रंग के कीड़े जो पत्तियों की निचली सतह और बालियों पर समूह में दिखते हैं। पत्तियां पीली पड़ जाती हैं, पौधा कमजोर होता है।\n\nआर्थिक हानि स्तर: 5-10 माहू प्रति पत्ती\n\nजैविक नियंत्रण:\n• लेडी बर्ड बीटल माहू को खाती है, इसे संरक्षित करें\n• नीम तेल 5 मिली/लीटर का छिड़काव\n• साबुन के पानी का छिड़काव (10 ग्राम/लीटर)\n\nरासायनिक नियंत्रण:\n• इमिडाक्लोप्रिड 17.8% SL 0.5 मिली/लीटर\n• थायामेथोक्सम 25% WG 0.2 ग्राम/लीटर\n• डाइमेथोएट 30% EC 2 मिली/लीटर\n\nनोट: शाम को छिड़काव करें, हवा न होने पर। लाभकारी कीटों का ध्यान रखें।",
        "crop_name": "wheat",
        "problem_type": "pest",
        "solution_steps": "1. माहू की संख्या गिनें (5-10/पत्ती से ज्यादा हो तो उपचार)\n2. पहले नीम तेल 5 मिली/लीटर ट्राई करें\n3. जरूरत पड़े तो इमिडाक्लोप्रिड 0.5 मिली/लीटर\n4. शाम को छिड़काव करें\n5. लेडी बर्ड बीटल को सुरक्षित रखें",
        "tags": "माहू,aphid,कीट,pest,imidacloprid,neem oil,insecticide",
        "language": "hi"
    },
    {
        "title": "गेहूं में सिंचाई प्रबंधन - समय और मात्रा",
        "content": "गेहूं में सही समय पर सिंचाई से उपज में 40-50% तक वृद्धि हो सकती है। गेहूं को 4-6 सिंचाई की जरूरत होती है।\n\nक्रांतिक अवस्थाएं (जब सिंचाई बहुत जरूरी है):\n1. CRI Stage (Crown Root Initiation): बुवाई के 20-25 दिन बाद - सबसे महत्वपूर्ण\n2. कल्ले फूटना (Tillering): 40-45 दिन\n3. गांठें बनना (Jointing): 60-65 दिन\n4. फूल आना (Flowering): 80-85 दिन\n5. दाना भरना (Grain filling): 100-105 दिन\n6. दूधिया अवस्था (Milking): 110-115 दिन\n\nपानी की मात्रा: हर सिंचाई में 5-7 सेमी पानी (500-700 घन मीटर/हेक्टेयर)\n\nध्यान दें:\n• CRI stage की सिंचाई छूटी तो उपज में 30% तक कमी\n• फूल आने और दाना भरने की सिंचाई भी बहुत महत्वपूर्ण\n• दोपहर में सिंचाई न करें, सुबह या शाम को करें\n• मिट्टी के अनुसार समय adjust करें",
        "crop_name": "wheat",
        "problem_type": "irrigation",
        "solution_steps": "1. CRI stage (20-25 दिन) - पहली और सबसे जरूरी\n2. कल्ले फूटना (40-45 दिन)\n3. गांठें बनना (60-65 दिन)\n4. फूल आना (80-85 दिन)\n5. दाना भरना (100-105 दिन)\n6. हर बार 5-7 सेमी पानी",
        "tags": "सिंचाई,irrigation,CRI stage,water management,critical stages",
        "language": "hi"
    },
    {
        "title": "गेहूं में खाद प्रबंधन - NPK और सूक्ष्म पोषक तत्व",
        "content": "संतुलित खाद का प्रयोग गेहूं की उच्च उपज के लिए अत्यंत महत्वपूर्ण है।\n\nमुख्य पोषक तत्व (प्रति हेक्टेयर):\n• नाइट्रोजन (N): 120 किलो\n• फॉस्फोरस (P): 60 किलो\n• पोटाश (K): 40 किलो\n\nखाद की मात्रा:\n• यूरिया: 260 किलो (46% N)\n• DAP (डीएपी): 130 किलो (18% N, 46% P)\n• MOP (म्यूरेट ऑफ पोटाश): 65 किलो (60% K)\n\nप्रयोग विधि:\n• DAP + MOP: बुवाई के समय पूरा\n• यूरिया: तीन बार में\n  - पहली बार: 85 किलो (20-25 दिन, CRI stage)\n  - दूसरी बार: 85 किलो (40-45 दिन, कल्ले फूटना)\n  - तीसरी बार: 90 किलो (60-65 दिन, गांठें बनना)\n\nसूक्ष्म पोषक तत्व:\n• जिंक सल्फेट: 25 किलो/हेक्टेयर (बुवाई से पहले मिट्टी में)\n• जिंक की कमी के लक्षण: पत्तियों पर सफेद धारियां\n\nध्यान: मिट्टी परीक्षण के आधार पर खाद की मात्रा adjust करें।",
        "crop_name": "wheat",
        "problem_type": "fertilizer",
        "solution_steps": "1. DAP 130 किलो + MOP 65 किलो बुवाई पर\n2. यूरिया पहली बार 85 किलो (20-25 दिन)\n3. यूरिया दूसरी बार 85 किलो (40-45 दिन)\n4. यूरिया तीसरी बार 90 किलो (60-65 दिन)\n5. जिंक सल्फेट 25 किलो बुवाई से पहले",
        "tags": "खाद,fertilizer,NPK,urea,DAP,zinc,यूरिया,fertilizer management",
        "language": "hi"
    }
]

async def populate_kb():
    """Populate kb_entries with wheat knowledge"""
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True
    )
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            print("🌾 Starting to populate wheat knowledge base...")
            
            for idx, entry_data in enumerate(WHEAT_KB_ENTRIES, 1):
                kb_entry = KBEntry(
                    title=entry_data["title"],
                    content=entry_data["content"],
                    crop_name=entry_data["crop_name"],
                    problem_type=entry_data["problem_type"],
                    solution_steps=entry_data["solution_steps"],
                    tags=entry_data["tags"],
                    is_approved=True,
                    is_banned=False,
                    language=entry_data["language"],
                    created_by="system",
                    created_at=datetime.now(timezone.utc)
                )
                
                session.add(kb_entry)
                print(f"✅ Added entry {idx}: {entry_data['title'][:50]}...")
            
            await session.commit()
            print(f"\n🎉 Successfully added {len(WHEAT_KB_ENTRIES)} knowledge base entries!")
            print("\n📊 Entries added:")
            for entry in WHEAT_KB_ENTRIES:
                print(f"  • {entry['title']}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(populate_kb())
