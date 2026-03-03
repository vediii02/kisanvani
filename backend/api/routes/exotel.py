from fastapi import APIRouter, Request, Response, Depends
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from db.session import get_db
from db.models.company import Company

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/incoming")
async def exotel_incoming(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Webhook endpoint hit by Exotel when a farmer calls the virtual number.
    Returns the XML needed to connect the call to the our WebSocket streaming endpoint.
    """
    form_data = await request.form()
    
    from_number = form_data.get('From', '')
    to_number = form_data.get('To', '')
    
    logger.info(f"Incoming call from {from_number} to {to_number}")
    
    # Construct the WebSocket URL based on the Request headers
    # Extract the host (e.g. 1234abcd.ngrok.app) and protocol
    host = request.headers.get("host")
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    
    # Map http/https to ws/wss
    ws_scheme = "wss" if scheme == "https" else "ws"
    
    stream_url = f"{ws_scheme}://{host}/ws/exotel"
    
    # Auto-detect company from the dialed To number
    url_params = ""
    if to_number:
        try:
            phone_suffix = to_number[-10:] if len(to_number) >= 10 else to_number
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
                logger.info(f"Resolved To number {to_number} to org_id: {db_org_id}, company_id: {db_company_id}")
            else:
                logger.warning(f"No company found for To number {to_number}")
        except Exception as e:
            logger.error(f"Error looking up company by phone: {e}")
            
    stream_url += url_params
    
    # Generate the Exotel compatible NCCO (XML format for call flow)
    xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{stream_url}">
        </Stream>
    </Connect>
</Response>"""
    
    return Response(content=xml_response, media_type="application/xml")
