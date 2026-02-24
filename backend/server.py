from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from api.routes import twilio_calling as twilio  
from core.config import settings
from core.logging import setup_logging
from voice.session_manager import session_manager
from voice.flow_manager import flow_manager
from api.routes import voice_gateway, kb, admin, calls, auth, superadmin, organisations, call_flow, products, organisation_admin, call_flow_v2, kb_upload
from api.routes import superadmin_platform, exotel_webhooks, analytics, farmer_profile, notifications, product_import, text_conversation, audio_conversation
from api.routes import org_phone_numbers, call_routing, test_form
from api.routes import superadmin_organisations, organisation_companies, admin_organisations, admin_companies, company_admin  # Multi-tenant routes
from api.routes.organisations import brand_router, product_router
from api.routes import exotel_passthru  # Production-ready Exotel Passthru webhook
from api.routes import exotel_calling  # NEW: Exotel Live Calling System


#----------------------------------rag endpoint import------------------------
from api.routes import rag_endpoint

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Kisan Vani AI Backend with MySQL")
    await session_manager.connect()
    await flow_manager.initialize()
    logger.info("Services initialized")
    yield
    logger.info("Shutting down")
    await session_manager.disconnect()

app = FastAPI(
    title="Kisan Vani AI",
    description="AI Voice Advisory Platform for Indian Farmers",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Allow all origins including file://
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)



# Include all routes
app.include_router(auth.router, prefix="/api")
## (Removed duplicate Twilio router include)
app.include_router(voice_gateway.router, prefix="/api")
app.include_router(kb.router, prefix="/api")
app.include_router(kb_upload.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(calls.router, prefix="/api")
app.include_router(call_flow.router, prefix="/api/call-flow", tags=["Call Flow"])
app.include_router(call_flow_v2.router, prefix="/api/call-flow", tags=["Call Flow V2"])
app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(organisation_admin.router, prefix="/api/org-admin", tags=["Organisation Admin"])
app.include_router(product_import.router, prefix="/api/org-admin/products/import", tags=["Product Import"])
app.include_router(superadmin.router, prefix="/api")
app.include_router(superadmin_platform.router, prefix="/api/superadmin", tags=["Super Admin Platform"])
app.include_router(superadmin_organisations.router, prefix="/api", tags=["Super Admin - Organisations"])  # Multi-tenant
app.include_router(admin_organisations.router, prefix="/api/admin", tags=["Admin - Organisations"])  # Admin role organisations
app.include_router(admin_companies.router, prefix="/api/admin", tags=["Admin - Companies"])  # Admin role companies
app.include_router(organisations.router, prefix="/api")
app.include_router(organisation_companies.router, prefix="/api", tags=["Organisation - Companies"])  # Multi-tenant
app.include_router(company_admin.router, prefix="/api", tags=["Company Admin"])  # Company self-management
app.include_router(brand_router, prefix="/api")
app.include_router(product_router, prefix="/api")


# New feature routes
app.include_router(exotel_webhooks.router, prefix="/api/exotel", tags=["Exotel Webhooks"])
app.include_router(exotel_calling.router, prefix="/api/exotel", tags=["Exotel Live Calling"])  # NEW: Production calling system
app.include_router(exotel_passthru.router, prefix="/webhooks/exotel", tags=["Exotel Passthru (Production)"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(farmer_profile.router, prefix="/api/farmers", tags=["Farmer Profile"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

# Multi-tenant phone number management and call routing
app.include_router(org_phone_numbers.router, prefix="/api", tags=["Organisation Phone Numbers"])
app.include_router(call_routing.router, prefix="/api", tags=["Call Routing"])
app.include_router(text_conversation.router, prefix="/api/conversation/text", tags=["Text Conversation"])
app.include_router(audio_conversation.router, prefix="/api/conversation/audio", tags=["Audio Conversation"])

# Test form API
app.include_router(test_form.router, prefix="/api", tags=["Test Form"])
# Twilio webhook route
app.include_router(twilio.router, prefix="/api", tags=["Twilio"])  # Twilio router include karo

# New feature routes
# app.include_router(exotel_webhooks.router, prefix="/api/exotel", tags=["Exotel Webhooks"])
# app.include_router(exotel_calling.router, prefix="/api/exotel", tags=["Exotel Live Calling"])  # NEW: Production calling system
# app.include_router(exotel_passthru.router, prefix="/webhooks/exotel", tags=["Exotel Passthru (Production)"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(farmer_profile.router, prefix="/api/farmers", tags=["Farmer Profile"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

# Multi-tenant phone number management and call routing
app.include_router(org_phone_numbers.router, prefix="/api", tags=["Organisation Phone Numbers"])
app.include_router(call_routing.router, prefix="/api", tags=["Call Routing"])
app.include_router(text_conversation.router, prefix="/api/conversation/text", tags=["Text Conversation"])
app.include_router(audio_conversation.router, prefix="/api/conversation/audio", tags=["Audio Conversation"])

# Test form API
app.include_router(test_form.router, prefix="/api", tags=["Test Form"])

# RAG API
app.include_router(rag_endpoint.router, tags=["RAG"])

# Ingestion API
from api.routes.ingest_documents import router as ingest_router

app.include_router(ingest_router)

# ============================================================================
# STATIC FILES FOR AUDIO SERVING (REQUIRED FOR EXOTEL <Play> TAG)
# ============================================================================
# Exotel's <Play> tag needs publicly accessible audio URLs
# We save TTS-generated audio and serve it via /static/audio/
# In production, use S3/GCS instead of local filesystem

audio_dir = Path("/app/static/audio")
audio_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="/app/static"), name="static")

@app.get("/api/")
async def root():
    return {
        "message": "Kisan Vani AI - Voice Advisory Platform",
        "version": "1.0.0",
        "status": "active",
        "database": "MySQL (Production)"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "database": "MySQL 10.11",
            "redis": "connected",
            "qdrant": "configured"
        }
    }

logger.info("✅ Kisan Vani AI Production Server with MySQL Started")
logger.info("🚀 Access API docs at: http://localhost:8001/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        
    )
