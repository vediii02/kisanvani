from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os
import traceback
import logging
from pathlib import Path
from dotenv import load_dotenv

from core.config import settings
from core.logging import setup_logging
from api.routes import kb, admin, auth, organisations, products
from api.routes import superadmin_platform, admin_organisations, admin_companies, organisation_companies  
from api.routes import pending_approvals  
from api.routes import organisation_pending_approvals 
from api.routes import company_profile 
from api.routes import company_brands
from api.routes import company_calls 
from api.routes.organisations import brand_router, product_router
from api.routes import exotel  
from services.voice.post_call_summary import generate_post_call_summary

# Voice bot components
from langchain_core.runnables import RunnableGenerator
from services.voice.stt_node import stt_stream
from services.voice.agent_node import agent_stream
from services.voice.tts_node import tts_stream
from services.voice.exotel_adapter import ExotelAdapter
from services.voice.session_context import (
    set_current_organisation_id,
    reset_current_organisation_id,
    set_current_company_id,
    reset_current_company_id,
    set_current_phone_number,
    reset_current_phone_number,
    set_current_session_id,
    reset_current_session_id,
    set_current_farmer_row_id,
    reset_current_farmer_row_id,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = setup_logging()

from fastapi.responses import JSONResponse
import sys

def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Kisan Vani AI Backend with PostgreSQL")
    
    # DB Ping
    try:
        from db.base import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database ping successful")
    except Exception as e:
        logger.exception("Database connection failed. Exiting.")
        sys.exit(1)

    # Initialize checkpointer at startup
    from services.voice.llm import init_checkpointer
    await init_checkpointer()

    logger.info("Services initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Kisan Vani AI",
    description="AI Voice Advisory Platform for Indian Farmers",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )

# Include all routes
app.include_router(auth.router, prefix="/api")
app.include_router(kb.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(superadmin_platform.router, prefix="/api/superadmin", tags=["Super Admin Platform"])
app.include_router(pending_approvals.router, prefix="/api/superadmin", tags=["Pending Approvals"])
app.include_router(organisation_pending_approvals.router, prefix="/api/organisation", tags=["Organisation Pending Approvals"])
app.include_router(admin_organisations.router, prefix="/api/admin", tags=["Admin - Organisations"])  # Admin role organisations
app.include_router(admin_companies.router, prefix="/api/admin", tags=["Admin - Companies"])  # Admin role companies
app.include_router(organisations.router, prefix="/api")
app.include_router(organisation_companies.router, prefix="/api", tags=["Organisation - Companies"])  # Multi-tenant
app.include_router(brand_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(company_profile.router, prefix="/api/company", tags=["Company Profile"])
app.include_router(company_brands.router, prefix="/api/company", tags=["Company Brands"])
app.include_router(company_calls.router, prefix="/api/company", tags=["Company Calls"])
app.include_router(exotel.router, prefix="/api/exotel", tags=["Exotel Setup"])


audio_dir = ROOT_DIR / "static" / "audio"
audio_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")

# Build the Conversational Voice Agent Pipeline
pipeline = (
    RunnableGenerator(stt_stream)        # Audio Bytes → STT Events
    | RunnableGenerator(agent_stream)    # STT Events → Agent Chunk Events (multi-turn conversation)
    | RunnableGenerator(tts_stream)      # Agent Chunk Events → TTS Audio Chunks
)


@app.websocket("/ws/conversation")
async def conversation_endpoint(websocket: WebSocket):
    await websocket.accept()
    organisation_id = _parse_optional_int(
        websocket.query_params.get("organisation_id") or websocket.query_params.get("org_id")
    )
    company_id = _parse_optional_int(websocket.query_params.get("company_id"))
    from_number = websocket.query_params.get("from_number") or websocket.query_params.get("phone")
    
    session_ctx_token = set_current_organisation_id(organisation_id)
    company_ctx_token = set_current_company_id(company_id)
    phone_ctx_token = set_current_phone_number(from_number)
    farmer_row_ctx_token = set_current_farmer_row_id(None)
    
    import uuid
    session_id = f"web_{uuid.uuid4().hex[:8]}"
    session_id_token = set_current_session_id(session_id)
    
    logger.info(f"Client connected to /ws/conversation - org: {organisation_id}, company: {company_id}, phone: {from_number}")
    
    async def websocket_audio_stream():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(websocket.receive_bytes(), timeout=2.0)
                    yield data
                except asyncio.TimeoutError:
                    yield b'\x00' * 1600
        except WebSocketDisconnect:
            logger.info("Client disconnected.")
        except Exception as e:
            logger.error(f"WebSocket read error: {e}")

    try:
        output_stream = pipeline.atransform(websocket_audio_stream())
        async for event in output_stream:
            try:
                if event.type == "barge_in":
                    await websocket.send_json({"type": "barge_in"})
                elif event.type == "stt_chunk":
                    await websocket.send_json({"type": "stt_chunk", "transcript": event.transcript})
                elif event.type == "stt_output":
                    logger.info(f"User said: {event.transcript}")
                    await websocket.send_json({"type": "stt_output", "transcript": event.transcript})
                elif event.type == "agent_chunk":
                    await websocket.send_json({"type": "agent_chunk", "text": event.text})
                elif event.type == "tts_chunk":
                    await websocket.send_bytes(event.audio)
            except WebSocketDisconnect:
                logger.info("Client disconnected during processing.")
                break
            except Exception as e:
                logger.error(f"Error resolving event: {e}", exc_info=True)
    except WebSocketDisconnect:
        logger.info("Client disconnected abruptly.")
    except Exception as e:
         logger.error(f"Pipeline execution error: {e}", exc_info=True)
    finally:
         reset_current_organisation_id(session_ctx_token)
         reset_current_company_id(company_ctx_token)
         reset_current_phone_number(phone_ctx_token)
         reset_current_session_id(session_id_token)
         reset_current_farmer_row_id(farmer_row_ctx_token)
         try:
             await websocket.close()
         except RuntimeError:
             pass

@app.websocket("/ws/exotel")
async def exotel_ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    organisation_id = _parse_optional_int(
        websocket.query_params.get("organisation_id") or websocket.query_params.get("org_id")
    )
    company_id = _parse_optional_int(websocket.query_params.get("company_id"))
    from_number = websocket.query_params.get("from_number") or websocket.query_params.get("phone")

    session_ctx_token = set_current_organisation_id(organisation_id)
    company_ctx_token = set_current_company_id(company_id)
    phone_ctx_token = set_current_phone_number(from_number)
    farmer_row_ctx_token = set_current_farmer_row_id(None)
    
    import uuid
    from datetime import datetime
    session_id = f"exotel_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
    session_id_token = set_current_session_id(session_id)
    
    logger.info(f"Exotel connected to /ws/exotel - org: {organisation_id}, company: {company_id}, phone: {from_number}")
    
    adapter = ExotelAdapter()
    call_active = True
    audio_queue: asyncio.Queue[tuple[str, str | bytes] | None] = asyncio.Queue(maxsize=256)

    async def _queue_audio(chunk: bytes) -> None:
        try:
            audio_queue.put_nowait(("media", chunk))
        except asyncio.QueueFull:
            # Drop oldest frame to keep real-time behavior under backpressure.
            try:
                _ = audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            audio_queue.put_nowait(("media", chunk))

    async def _handle_start_event(message: str) -> None:
        nonlocal organisation_id, company_id, session_ctx_token, company_ctx_token
        nonlocal from_number, phone_ctx_token, farmer_row_ctx_token

        try:
            import json
            data = json.loads(message)
            custom_params = data.get("start", {}).get("custom_parameters", {})
            cp_org_id = _parse_optional_int(custom_params.get("organisation_id") or custom_params.get("org_id"))
            cp_company_id = _parse_optional_int(custom_params.get("company_id"))

            changed = False
            if cp_org_id and cp_org_id != organisation_id:
                organisation_id = cp_org_id
                reset_current_organisation_id(session_ctx_token)
                session_ctx_token = set_current_organisation_id(organisation_id)
                changed = True
            if cp_company_id and cp_company_id != company_id:
                company_id = cp_company_id
                reset_current_company_id(company_ctx_token)
                company_ctx_token = set_current_company_id(company_id)
                changed = True
            if changed:
                logger.info(f"Context updated from custom_params: org={organisation_id}, company={company_id}")

        except Exception as e:
            logger.warning(f"Could not parse custom_parameters: {e}")

        if not company_id:  # Only try to find company if not already set by custom_parameters
            try:
                from db.base import AsyncSessionLocal
                from db.models.company import Company
                from sqlalchemy import select, or_
                async with AsyncSessionLocal() as db:
                    found = False

                    # Strategy 1: Look up company by the 'to' number (works if each company has unique ExoPhone)
                    if adapter.to_number:
                        phone_suffix = adapter.to_number[-10:] if len(adapter.to_number) >= 10 else adapter.to_number
                        stmt = select(Company.id, Company.organisation_id).where(
                            or_(
                                Company.phone.like(f"%{phone_suffix}"),
                                Company.secondary_phone.like(f"%{phone_suffix}")
                            )
                        )
                        result = await db.execute(stmt)
                        company_row = result.first()
                        if company_row:
                            db_company_id, db_org_id = company_row
                            company_id = db_company_id
                            reset_current_company_id(company_ctx_token)
                            company_ctx_token = set_current_company_id(company_id)
                            if not organisation_id:
                                organisation_id = db_org_id
                                reset_current_organisation_id(session_ctx_token)
                                session_ctx_token = set_current_organisation_id(organisation_id)
                            found = True
                            logger.info(f"Context resolved from To number: org={organisation_id}, company={company_id}")

                    # Strategy 3: Fallback to first company in DB (for testing / single-tenant)
                    if not found:
                        fallback_stmt = select(Company.id, Company.organisation_id).limit(1)
                        fallback_result = await db.execute(fallback_stmt)
                        fallback_row = fallback_result.first()
                        if fallback_row:
                            db_company_id, db_org_id = fallback_row
                            company_id = db_company_id
                            reset_current_company_id(company_ctx_token)
                            company_ctx_token = set_current_company_id(company_id)
                            if not organisation_id:
                                organisation_id = db_org_id
                                reset_current_organisation_id(session_ctx_token)
                                session_ctx_token = set_current_organisation_id(organisation_id)
                            logger.warning(f"FALLBACK: Using default company: org={organisation_id}, company={company_id}")
            except Exception as e:
                logger.error(f"Error looking up company by phone: {e}")

        # Also update phone number if available in adapter
        if adapter.from_number and adapter.from_number != from_number:
            from_number = adapter.from_number
            reset_current_phone_number(phone_ctx_token)
            phone_ctx_token = set_current_phone_number(from_number)
            reset_current_farmer_row_id(farmer_row_ctx_token)
            farmer_row_ctx_token = set_current_farmer_row_id(None)
            logger.info(f"Phone number updated from Exotel: {from_number}")

        try:
            from db.base import AsyncSessionLocal
            from db.models.call_session import CallSession, CallStatus
            from db.models.farmer import Farmer
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                farmer_id = None
                if adapter.from_number:
                    phone_search = adapter.from_number[-10:] if len(adapter.from_number) >= 10 else adapter.from_number
                    farmer_stmt = select(Farmer).where(Farmer.phone_number.like(f"%{phone_search}"))
                    farmer_result = await db.execute(farmer_stmt)
                    farmer = farmer_result.scalars().first()
                    if farmer:
                        farmer_id = farmer.id
                    else:
                        new_farmer = Farmer(
                            phone_number=adapter.from_number,
                            name="Unknown Caller",
                            language="hi"
                        )
                        db.add(new_farmer)
                        await db.commit()
                        await db.refresh(new_farmer)
                        farmer_id = new_farmer.id
                        logger.info(f"Created new Farmer {farmer_id} for number {adapter.from_number}")

                new_call = CallSession(
                    session_id=session_id,
                    phone_number=from_number or adapter.from_number or "Unknown",
                    provider_name="exotel",
                    provider_call_id=adapter.call_sid,
                    status=CallStatus.ACTIVE,
                    organisation_id=organisation_id,
                    from_phone=adapter.from_number,
                    to_phone=adapter.to_number,
                    exotel_call_sid=adapter.call_sid,
                    call_direction="inbound",
                    farmer_id=farmer_id
                )
                db.add(new_call)
                await db.commit()
                logger.info(f"Created CallSession for {adapter.call_sid} (Farmer ID: {farmer_id})")
        except Exception as e:
            logger.error(f"Error creating CallSession: {e}")

    async def exotel_reader():
        nonlocal call_active
        try:
            while call_active:
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    event, pcm_bytes = adapter.parse_message(message)

                    if event == "connected":
                        continue
                    if event == "start":
                        try:
                            audio_queue.put_nowait(("start", message))
                        except asyncio.QueueFull:
                            pass
                        continue
                    if event == "stop":
                        logger.info("Exotel sent stop event")
                        try:
                            audio_queue.put_nowait(("stop", ""))
                        except asyncio.QueueFull:
                            pass
                        call_active = False
                        break
                    if pcm_bytes:
                        await _queue_audio(pcm_bytes)

                except asyncio.TimeoutError:
                    await _queue_audio(b"\x00" * 1600)
                except WebSocketDisconnect:
                    logger.info("Exotel websocket disconnected by peer")
                    call_active = False
                    break
                except Exception as e:
                    logger.error(f"Exotel reader error: {e}", exc_info=True)
                    await asyncio.sleep(0.1)
        finally:
            call_active = False
            try:
                audio_queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

    async def exotel_audio_stream():
        nonlocal call_active
        reader_task = asyncio.create_task(exotel_reader())
        try:
            while call_active or not audio_queue.empty():
                item = await audio_queue.get()
                if item is None:
                    break
                item_type, payload = item
                if item_type == "start":
                    await _handle_start_event(str(payload))
                    continue
                if item_type == "stop":
                    call_active = False
                    break
                if item_type == "media":
                    yield bytes(payload)
        finally:
            reader_task.cancel()
            try:
                await reader_task
            except asyncio.CancelledError:
                pass

    try:
        output_stream = pipeline.atransform(exotel_audio_stream())
        async for event in output_stream:
            if not call_active:
                break
            try:
                if event.type == "barge_in":
                    msg = adapter.format_barge_in_message()
                    if msg:
                        await websocket.send_text(msg)
                elif event.type == "tts_chunk":
                    exotel_msg = adapter.format_audio_message(event.audio)
                    if exotel_msg:
                        await websocket.send_text(exotel_msg)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error sending to Exotel: {e}")
    except Exception as e:
         logger.error(f"Exotel Pipeline execution error: {e}", exc_info=True)
    finally:
         reset_current_organisation_id(session_ctx_token)
         reset_current_company_id(company_ctx_token)
         reset_current_phone_number(phone_ctx_token)
         reset_current_session_id(session_id_token)
         reset_current_farmer_row_id(farmer_row_ctx_token)
         
         # Update CallSession to COMPLETED
         try:
             from db.base import AsyncSessionLocal
             from db.models.call_session import CallSession, CallStatus
             from sqlalchemy import select
             from datetime import datetime, timezone
             if adapter and adapter.call_sid:
                 async with AsyncSessionLocal() as db:
                     call_obj = (await db.execute(select(CallSession).where(CallSession.provider_call_id == adapter.call_sid))).scalar_one_or_none()
                     if call_obj:
                         call_obj.status = CallStatus.COMPLETED
                         call_obj.end_time = datetime.now(timezone.utc)
                         if call_obj.start_time:
                             call_obj.duration_seconds = int((call_obj.end_time - call_obj.start_time).total_seconds())
                         await db.commit()
                         logger.info(f"Updated CallSession {adapter.call_sid} to COMPLETED")
                         
                         # Trigger post-call summarization
                         asyncio.create_task(generate_post_call_summary(
                             session_id=call_obj.session_id,
                             provider_call_id=call_obj.provider_call_id,
                             organisation_id=call_obj.organisation_id,
                             company_id=company_id
                         ))
         except Exception as e:
             logger.error(f"Error updating CallSession status: {e}")

         try:
             await websocket.close()
         except RuntimeError:
             pass


@app.get("/api/")
async def root():
    return {
        "message": "Kisan Vani AI - Voice Advisory Platform",
        "version": "1.0.0",
        "status": "active",
        "database": "PostgreSQL"
    }

@app.get("/api/health")
async def health_check():
    health = {
        "status": "healthy",
        "system": "operational",
        "services": {
            "database": "disconnected",
            "redis": "disconnected"
        },
        "active_alerts": 0
    }
    
    # 1. DB Check
    try:
        from db.base import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health["services"]["database"] = "connected"
    except Exception:
        health["status"] = "unhealthy"
        health["system"] = "degraded"
        
    # 2. Redis Check
    try:
        import redis.asyncio as redis
        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        await r.ping()
        health["services"]["redis"] = "connected"
    except Exception:
        health["services"]["redis"] = "disconnected"
        

    # 4. Active Alerts Check (Critical Audit Logs in last 24h)
    try:
        from db.base import AsyncSessionLocal
        from db.models.audit import AuditLog
        from sqlalchemy import select, func
        from datetime import datetime, timedelta, timezone
        
        async with AsyncSessionLocal() as db:
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            stmt = select(func.count(AuditLog.id)).where(
                AuditLog.severity == "critical",
                AuditLog.timestamp >= yesterday
            )
            result = await db.execute(stmt)
            health["active_alerts"] = result.scalar()
    except Exception:
        pass

    return health

logger.info("✅ Kisan Vani AI Production Server with PostgreSQL Started")
api_host = os.getenv("API_HOST", "0.0.0.0")
api_port = os.getenv("API_PORT", "8001")
logger.info("🚀 Access API docs at: http://%s:%s/docs", api_host, api_port)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        
    )
