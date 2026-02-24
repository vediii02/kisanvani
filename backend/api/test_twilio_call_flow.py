import asyncio
import pytest
from fastapi.testclient import TestClient
from backend.api.routes.twilio_calling import router
from backend.db.session import get_db
from backend.db.models.farmer import Farmer
from backend.db.models.call_session import CallSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# NOTE: This is a simplified test. In real use, use a full test DB and fixtures.

client = TestClient(router)

# TEST_PHONE = "+441234567890"
CALL_SID = "TESTCALLSID123"

TEST_PHONE = "+1 234 414 5643"
# CALL_SID = "CA789e23569feeec0c7aefd31729fa0955"

PROFILE_ANSWERS = [
    ("name", "राम कुमार"),
    ("village", "अलवर"),
    ("district", "अलवर"),
    ("state", "राजस्थान"),
    ("crop_type", "गेहूं"),
    ("land_size", "10"),
    ("crop_area", "8"),
    ("problem_area", "2"),
    ("language", "हिंदी"),
]

async def get_farmer_row(db: AsyncSession, phone=TEST_PHONE):
    result = await db.execute(select(Farmer).where(Farmer.phone_number == phone).order_by(Farmer.id.desc()))
    return result.scalars().first()

async def get_call_session(db: AsyncSession, sid=CALL_SID):
    result = await db.execute(select(CallSession).where(CallSession.session_id == sid))
    return result.scalars().first()

def test_profile_flow(monkeypatch):
    # Simulate the call session and farmer creation/update
    db = next(get_db())
    # Clean up any previous test data
    db.execute(f"DELETE FROM call_sessions WHERE session_id='{CALL_SID}'")
    db.execute(f"DELETE FROM farmers WHERE phone_number='{TEST_PHONE}'")
    db.commit()

    # Simulate each profile question
    for idx, (field, answer) in enumerate(PROFILE_ANSWERS):
        form = {
            "CallSid": CALL_SID,
            "SpeechResult": answer,
            "From": TEST_PHONE
        }
        # Simulate POST to /twilio/next-step
        response = client.post("/twilio/next-step", data=form)
        assert response.status_code == 200

    # Check only one farmer row exists and all fields are filled
    farmer = asyncio.run(get_farmer_row(db))
    assert farmer is not None
    for field, answer in PROFILE_ANSWERS:
        assert getattr(farmer, field) == answer

    # Check only one farmer row for this phone
    result = db.execute(f"SELECT COUNT(*) FROM farmers WHERE phone_number='{TEST_PHONE}'")
    count = result.fetchone()[0]
    assert count == 1

    # Clean up
    db.execute(f"DELETE FROM call_sessions WHERE session_id='{CALL_SID}'")
    db.execute(f"DELETE FROM farmers WHERE phone_number='{TEST_PHONE}'")
    db.commit()
