from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from db.session import get_db
from db.models.company import Company

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/incoming")
@router.get("/incoming")
async def exotel_incoming(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Voicebot applet endpoint hit by Exotel for each incoming call.
    Returns JSON with the dynamic WSS URL containing company context.
    Handles both POST (form data) and GET (query parameters) requests.
    """
    if request.method == "POST":
        form_data = await request.form()
    else:
        form_data = request.query_params
    
    # Log ALL incoming parameters for debugging
    all_params = {key: form_data.get(key) for key in form_data}
    logger.info(f"=== EXOTEL VOICEBOT WEBHOOK === {all_params}")
    
    from_number = form_data.get('From', '') or form_data.get('CallFrom', '')
    to_number = form_data.get('To', '') or form_data.get('CallTo', '')
    
    # Construct the WebSocket URL
    host = request.headers.get("host")
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    ws_scheme = "wss" if scheme == "https" else "ws"
    stream_url = f"{ws_scheme}://{host}/ws/exotel"
    
    # Try to identify the company from available data
    original_dialed_number = form_data.get('DialWhomNumber') or form_data.get('ForwardedFrom')
    if original_dialed_number and original_dialed_number.strip() == '':
        original_dialed_number = None
    
    lookup_number = original_dialed_number if original_dialed_number else to_number
    
    logger.info(f"Voicebot Webhook | From: {from_number} | To: {to_number} | OriginalDialed: {original_dialed_number} | Lookup: {lookup_number}")
    
    # Auto-detect company from the lookup number
    url_params = ""
    company_found = False
    if lookup_number:
        try:
            phone_suffix = lookup_number[-10:] if len(lookup_number) >= 10 else lookup_number
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
                url_params = f"?org_id={db_org_id}&company_id={db_company_id}"
                company_found = True
                logger.info(f"Resolved number {lookup_number} → org_id: {db_org_id}, company_id: {db_company_id}")
            else:
                logger.warning(f"No company found for number {lookup_number}")
        except Exception as e:
            logger.error(f"Error looking up company by phone: {e}")
    
    # Fallback: use first company in DB
    if not company_found:
        try:
            fallback_stmt = select(Company.id, Company.organisation_id).limit(1)
            fallback_result = await db.execute(fallback_stmt)
            fallback_row = fallback_result.first()
            if fallback_row:
                db_company_id, db_org_id = fallback_row
                url_params = f"?org_id={db_org_id}&company_id={db_company_id}"
                logger.warning(f"FALLBACK: Using default company → org_id: {db_org_id}, company_id: {db_company_id}")
        except Exception as e:
            logger.error(f"Error in fallback company lookup: {e}")

    stream_url += url_params
    
    logger.info(f"Returning dynamic WSS URL: {stream_url}")
    
    # Return JSON with the WSS URL — this is what Exotel's Voicebot applet expects
    return JSONResponse(content={"url": stream_url})
