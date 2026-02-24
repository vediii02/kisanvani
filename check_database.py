#!/usr/bin/env python3
"""
Simple Database Check - Verify Farmer Table Structure and Data
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from db.base import AsyncSessionLocal
from db.models.farmer import Farmer


async def check_database():
    """Check farmer table structure and data"""
    
    print("\n" + "=" * 70)
    print("🗄️  DATABASE STRUCTURE AND DATA CHECK")
    print("=" * 70)
    
    db = AsyncSessionLocal()
    
    try:
        # Check table structure
        print("\n1️⃣  Checking farmers table structure...")
        result = await db.execute(text("DESCRIBE farmers"))
        columns = result.fetchall()
        
        print("\n   📋 Farmers Table Columns:")
        print("   " + "-" * 66)
        print(f"   {'Field':<20} {'Type':<25} {'Null':<6} {'Key':<6}")
        print("   " + "-" * 66)
        for col in columns:
            field, type_, null, key = col[0], col[1], col[2], col[3]
            print(f"   {field:<20} {type_:<25} {null:<6} {key:<6}")
        print("   " + "-" * 66)
        
        # Count farmers
        print("\n2️⃣  Counting farmers in database...")
        result = await db.execute(select(Farmer))
        farmers = result.scalars().all()
        print(f"   📊 Total farmers: {len(farmers)}")
        
        # Show sample farmers
        if farmers:
            print("\n3️⃣  Sample farmer records:")
            print("   " + "-" * 66)
            for i, farmer in enumerate(farmers[:5], 1):
                print(f"\n   Farmer #{i}:")
                print(f"      ID:           {farmer.id}")
                print(f"      Phone:        {farmer.phone_number}")
                print(f"      Name:         {farmer.name or '(empty)'}")
                print(f"      Village:      {farmer.village or '(empty)'}")
                print(f"      District:     {farmer.district or '(empty)'}")
                print(f"      State:        {farmer.state or '(empty)'}")
                print(f"      Crop Type:    {farmer.crop_type or '(empty)'}")
                print(f"      Land Size:    {farmer.land_size or '(empty)'}")
                print(f"      Created:      {farmer.created_at}")
            
            if len(farmers) > 5:
                print(f"\n   ... and {len(farmers) - 5} more farmers")
        else:
            print("\n   ℹ️  No farmers in database yet")
        
        # Statistics
        print("\n4️⃣  Field completion statistics:")
        if farmers:
            fields_stats = {
                'name': sum(1 for f in farmers if f.name),
                'village': sum(1 for f in farmers if f.village),
                'district': sum(1 for f in farmers if f.district),
                'state': sum(1 for f in farmers if f.state),
                'crop_type': sum(1 for f in farmers if f.crop_type),
                'land_size': sum(1 for f in farmers if f.land_size),
            }
            
            total = len(farmers)
            print("   " + "-" * 66)
            for field, count in fields_stats.items():
                percentage = (count / total * 100) if total > 0 else 0
                print(f"   {field:<15} {count:>3}/{total:<3} ({percentage:>5.1f}%)")
            print("   " + "-" * 66)
        else:
            print("   ℹ️  No data to analyze")
        
        print("\n" + "=" * 70)
        print("✅ Database check complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()


async def main():
    await check_database()


if __name__ == "__main__":
    asyncio.run(main())
