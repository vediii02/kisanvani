#!/usr/bin/env python3
"""
Farmer Information Auto-Save Demo
Demonstrates how farmer information is automatically extracted and saved
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from nlu.entity_extractor import extract_all_farmer_entities


def demo():
    """Run demo of farmer information extraction"""
    
    print("\n" + "=" * 80)
    print("🌾 FARMER INFORMATION AUTO-SAVE FEATURE DEMO")
    print("=" * 80)
    
    print("\n📝 यह feature automatically किसान की information extract करके database में save")
    print("   करता है। किसान को कुछ extra बताने की ज़रूरत नहीं!")
    
    # Sample conversations
    conversations = [
        {
            "title": "Example 1: Basic Introduction",
            "messages": [
                "नमस्ते, मेरा नाम राम सिंह है",
                "मैं रामपुर गांव से हूं",
                "जिला बिजनौर, उत्तर प्रदेश"
            ]
        },
        {
            "title": "Example 2: Complete Information in One Message",
            "messages": [
                "मैं मोहन लाल हूं, कमलापुर गाँव, मेरठ जिला, उत्तर प्रदेश से",
            ]
        },
        {
            "title": "Example 3: Farm Details",
            "messages": [
                "मेरे पास 5 एकड़ जमीन है",
                "गेहूं की खेती करता हूं"
            ]
        },
        {
            "title": "Example 4: Mixed Information",
            "messages": [
                "नाम सुरेश कुमार है, शामली गांव से",
                "10 bigha जमीन पर धान उगाता हूं"
            ]
        }
    ]
    
    for i, conversation in enumerate(conversations, 1):
        print("\n" + "-" * 80)
        print(f"📌 {conversation['title']}")
        print("-" * 80)
        
        all_extracted = {}
        
        for msg_num, message in enumerate(conversation['messages'], 1):
            print(f"\n💬 Farmer Message {msg_num}: \"{message}\"")
            
            # Extract entities
            entities = extract_all_farmer_entities(message)
            
            # Show extracted information
            extracted_this_turn = []
            for key, value in entities.items():
                if value:
                    all_extracted[key] = value
                    extracted_this_turn.append(f"{key}: {value}")
            
            if extracted_this_turn:
                print(f"   ✅ Extracted: {', '.join(extracted_this_turn)}")
            else:
                print(f"   ℹ️  No new information extracted")
        
        # Show cumulative extraction
        print(f"\n📊 Complete Farmer Profile Built:")
        if all_extracted:
            for key, value in all_extracted.items():
                if key != 'crop':  # Skip duplicate crop entry
                    print(f"   • {key.replace('_', ' ').title()}: {value}")
        else:
            print("   ℹ️  No information extracted")
        
        print(f"\n💾 This information would be automatically saved to database!")
    
    # Show database schema
    print("\n" + "=" * 80)
    print("📋 DATABASE SCHEMA - farmers table")
    print("=" * 80)
    print("""
    ┌─────────────────┬──────────────┬─────────────────────────────────┐
    │ Field           │ Type         │ Description                      │
    ├─────────────────┼──────────────┼─────────────────────────────────┤
    │ id              │ INT          │ Primary key                      │
    │ phone_number    │ VARCHAR(15)  │ Contact number (unique)          │
    │ name            │ VARCHAR(200) │ किसान का नाम                     │
    │ village         │ VARCHAR(200) │ गांव                             │
    │ district        │ VARCHAR(200) │ जिला                             │
    │ state           │ VARCHAR(200) │ राज्य                            │
    │ crop_type       │ VARCHAR(200) │ मुख्य फसल                        │
    │ land_size       │ VARCHAR(50)  │ जमीन का साइज़                    │
    │ language        │ VARCHAR(10)  │ भाषा (default: hi)               │
    │ status          │ ENUM         │ ACTIVE/INACTIVE                  │
    │ created_at      │ DATETIME     │ Registration date                │
    │ updated_at      │ DATETIME     │ Last update                      │
    └─────────────────┴──────────────┴─────────────────────────────────┘
    """)
    
    # Show benefits
    print("\n" + "=" * 80)
    print("✨ KEY BENEFITS")
    print("=" * 80)
    print("""
    ✅ Automatic - किसान को extra form भरने की ज़रूरत नहीं
    ✅ Natural - Normal conversation में ही information collect होती है
    ✅ Flexible - Hindi, Hinglish, English सभी में काम करता है
    ✅ Smart - Different patterns में बोलने पर भी समझ लेता है
    ✅ Safe - Existing data overwrite नहीं होता
    ✅ Non-intrusive - Conversation flow में कोई रुकावट नहीं
    """)
    
    print("\n" + "=" * 80)
    print("🚀 FEATURE STATUS: ✅ IMPLEMENTED & READY")
    print("=" * 80)
    print()


if __name__ == "__main__":
    demo()
