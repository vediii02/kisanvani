#!/usr/bin/env python3
"""
Quick test script for call routing
"""
import asyncio
import sys
sys.path.insert(0, '/home/ubuntu/Desktop/kisan/kisan-main/backend')

async def test_call_routing():
    from db.session import AsyncSessionLocal
    from services.call_routing_service import call_routing_service
    
    print("🧪 Testing Call Routing Service")
    print("=" * 50)
    
    async with AsyncSessionLocal() as db:
        # Test incoming call
        from_phone = "+919876543210"
        to_phone = "9999888877"
        
        print(f"📞 Testing call from {from_phone} to {to_phone}")
        
        try:
            call_session, error = await call_routing_service.handle_incoming_call(
                db=db,
                from_phone=from_phone,
                to_phone=to_phone,
                source="simulator"
            )
            
            if error:
                print(f"❌ Error: {error}")
            else:
                print(f"✅ Success!")
                print(f"   Call Session ID: {call_session.id}")
                print(f"   Session ID: {call_session.session_id}")
                print(f"   Farmer ID: {call_session.farmer_id}")
                print(f"   Status: {call_session.status}")
                
        except Exception as e:
            print(f"💥 Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_call_routing())
