import asyncio
import os
import uuid
import re
from typing import Any
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from openai import AsyncOpenAI
from sqlalchemy import select, func

from db.base import AsyncSessionLocal
from db.models.knowledge_base import KnowledgeEntry
from db.models.conversation_memory import ConversationMemory
from services.voice.session_context import get_current_organisation_id, get_current_company_id
from services.config_service import get_platform_config
from services.voice.chroma_service import chroma_service

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

from services.voice.logger import setup_logger
logger = setup_logger("llm")

# ==========================================
# 1. Initialize Components
# ==========================================

# LLM factory — picks provider based on PlatformConfig
def _create_groq_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=groq_api_key,
    )

def _create_openai_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=openai_api_key,
    )

def _create_gemini_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
        google_api_key=api_key,
    )

# Default LLM (used as fallback)
llm = _create_groq_llm()

async def get_llm():
    """Get the LLM based on current PlatformConfig."""
    try:
        config = await get_platform_config()
        provider = config.get("llm_model", "groq")
        if provider == "openai":
            logger.info("Using OpenAI (GPT-4o) as LLM provider")
            return _create_openai_llm()
        elif provider == "gemini":
            logger.info("Using Google (Gemini 2.0 Flash) as LLM provider")
            return _create_gemini_llm()
        else:
            logger.info("Using Groq (Llama 3.3) as LLM provider")
            return _create_groq_llm()
    except Exception as e:
        logger.error(f"Failed to get LLM from config, using default Groq: {e}")
        return _create_groq_llm()

openai_client = AsyncOpenAI(api_key=openai_api_key)

from collections import OrderedDict

# Maximum number of agent graphs to keep in memory to prevent memory leaks
MAX_AGENT_CACHE_SIZE = 100
_agent_cache: OrderedDict[tuple[int | None, int | None, str], Any] = OrderedDict()

# Postgres-backed conversation memory
_pg_host = os.getenv("PG_HOST", "localhost")
_pg_port = os.getenv("PG_PORT", "5432")
_pg_user = os.getenv("PG_USER", "kisanvani")
_pg_pass = os.getenv("PG_PASSWORD", "rootpassword")
_pg_db = os.getenv("PG_DATABASE", "kisanvani")
_pg_conn_str = f"postgresql://{_pg_user}:{_pg_pass}@{_pg_host}:{_pg_port}/{_pg_db}"

checkpointer = None

async def init_checkpointer():
    global checkpointer
    if checkpointer is not None:
        return
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool
        pool = AsyncConnectionPool(conninfo=_pg_conn_str, open=False, kwargs={"autocommit": True})
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        logger.info("AsyncPostgresSaver checkpointer initialized")
    except Exception as e:
        logger.error(f"Checkpointer init failed, falling back to in-memory: {e}")
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()


# ==========================================
# 2. Embedding + RAG Retrieval
# ==========================================
async def _fetch_query_embedding_google(query: str) -> list[float]:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    return await embeddings.aembed_query(query)

async def _fetch_query_embedding_openai(query: str) -> list[float]:
    response = await openai_client.embeddings.create(
        input=query,
        model="text-embedding-3-small",
    )
    return response.data[0].embedding

async def fetch_embedding(text: str) -> list[float]:
    try:
        config = await get_platform_config()
        provider = config.get("llm_model", "groq")
        if provider == "gemini":
            logger.info("Using Google Gemini for embeddings")
            return await _fetch_query_embedding_google(text)
    except Exception as e:
        logger.error(f"Failed to get PlatformConfig for embedding dict, falling back to OpenAI: {e}")
    
    logger.info("Using OpenAI text-embedding-3-small for embeddings")
    return await _fetch_query_embedding_openai(text)


async def _pgvector_search(
    query: str,
    *,
    limit: int = 5,
    min_confidence: float = 20.0,
    organisation_id: int,
    company_id: int | None = None,
) -> list[KnowledgeEntry]:
    query_vector = await fetch_embedding(query)

    async with AsyncSessionLocal() as db:
        # Distance = 1 - CosineSimilarity
        # Confidence = (1 - Distance) * 100
        distance_col = KnowledgeEntry.embedding.cosine_distance(query_vector)
        confidence_expr = (1 - distance_col) * 100

        filters = [
            KnowledgeEntry.embedding.is_not(None),
            KnowledgeEntry.organisation_id == organisation_id,
            confidence_expr >= min_confidence
        ]
        if company_id is not None:
            filters.append(KnowledgeEntry.company_id == company_id)
            
        stmt = (
            select(KnowledgeEntry)
            .where(*filters)
        )
        stmt = stmt.order_by(
            KnowledgeEntry.embedding.cosine_distance(query_vector)
        ).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

async def save_conversation_memory(phone_number: str, role: str, content: str, metadata: dict | None = None) -> None:
    """Save a piece of conversation memory with its embedding."""
    if not phone_number or not content:
        return
    try:
        embedding = await fetch_embedding(content)
        async with AsyncSessionLocal() as db:
            from sqlalchemy import insert
            stmt = insert(ConversationMemory).values(
                phone_number=phone_number,
                role=role,
                content=content,
                embedding=embedding,
                metadata_json=metadata
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(f"Saved {role} memory for {phone_number}: {content[:50]}...")
    except Exception as e:
        logger.error(f"Failed to save conversation memory: {e}")

async def search_conversation_memory(phone_number: str, query: str, limit: int = 3, min_confidence: float = 30.0) -> str:
    """Search for relevant past memories for a phone number."""
    if not phone_number or not query:
        return ""
    try:
        # Optimization 4: Fast COUNT check before expensive embedding call
        async with AsyncSessionLocal() as db:
            count = await db.scalar(
                select(func.count(ConversationMemory.id))
                .where(ConversationMemory.phone_number == phone_number)
            )
            if count == 0:
                return ""

        query_vector = await fetch_embedding(query)
        async with AsyncSessionLocal() as db:
            distance_col = ConversationMemory.embedding.cosine_distance(query_vector)
            confidence_expr = (1 - distance_col) * 100
            stmt = (
                select(ConversationMemory)
                .where(
                    ConversationMemory.phone_number == phone_number,
                    ConversationMemory.embedding.is_not(None),
                    confidence_expr >= min_confidence
                )
                .order_by(distance_col)
                .limit(limit)
            )
            result = await db.execute(stmt)
            memories = result.scalars().all()
            if not memories:
                return ""
            
            context = "\n".join([f"- {mem.content}" for mem in memories])
            return context
    except Exception as e:
        logger.error(f"Failed to search conversation memory: {e}")
        return ""


async def _fetch_farmer_profile(farmer_row_id: int | None) -> str:
    """Optimization 5: Reusable async helper for farmer profile fetch."""
    if not farmer_row_id:
        return ""
    try:
        from db.models.farmer import Farmer
        async with AsyncSessionLocal() as db:
            farmer = await db.get(Farmer, farmer_row_id)
            if not farmer:
                return ""
            parts = []
            if farmer.name: parts.append(f"Name: {farmer.name}")
            if farmer.village: parts.append(f"Village: {farmer.village}")
            if farmer.district: parts.append(f"District: {farmer.district}")
            if farmer.state: parts.append(f"State: {farmer.state}")
            if farmer.crop_type: parts.append(f"Crop: {farmer.crop_type}")
            if farmer.land_size: parts.append(f"Land Size: {farmer.land_size}")
            if farmer.crop_area: parts.append(f"Crop Area: {farmer.crop_area}")
            if farmer.problem_area: parts.append(f"Problem Area: {farmer.problem_area}")
            if farmer.crop_age_days: parts.append(f"Crop Age (days): {farmer.crop_age_days}")
            return " | ".join(parts) if parts else ""
    except Exception as e:
        logger.error(f"Error fetching farmer profile: {e}")
        return ""


# ==========================================
# 3. Tools
# ==========================================
@tool
async def retrieve_context(query: str, organisation_id: int | None = None, company_id: int | None = None) -> str:
    """Use this tool ONLY when the farmer asks for treatment, medicine, or solution for crop disease.
    DO NOT guess answers; always use this tool if advice is needed.

    Args:
        query: Search query (crop name + symptoms).
        organisation_id: Optional tenant scope ID.
        company_id: Optional sub-tenant company ID.
    """
    logger.info("RAG retrieval: query=%r org_id=%r company_id=%r", query, organisation_id, company_id)

    resolved_org_id = organisation_id
    if resolved_org_id is None:
        from services.voice.session_context import get_current_organisation_id
        resolved_org_id = get_current_organisation_id()
    
    resolved_comp_id = company_id
    if resolved_comp_id is None:
        from services.voice.session_context import get_current_company_id
        resolved_comp_id = get_current_company_id()

    # Fallback to DB lookup if context is missing (common in live async loops)
    if resolved_org_id is None:
        from services.voice.session_context import get_current_session_id
        session_id = get_current_session_id()
        if session_id:
            try:
                from db.models.call_session import CallSession
                from services.voice.session_context import set_current_organisation_id, set_current_company_id
                async with AsyncSessionLocal() as db:
                    call_row = (await db.execute(
                        select(CallSession.organisation_id)
                        .where(CallSession.session_id == session_id)
                    )).first()
                    if call_row:
                        db_org_id = call_row[0]
                        if db_org_id:
                            resolved_org_id = db_org_id
                            set_current_organisation_id(db_org_id)
                            logger.info("Recovered organisation_id=%s from session DB", db_org_id)
            except Exception as e:
                logger.warning("Failed to recover org_id from session DB: %s", e)

    if resolved_org_id is None:
        env_org_id = os.getenv("VOICE_DEFAULT_ORGANISATION_ID")
        resolved_org_id = int(env_org_id) if env_org_id else None

    if resolved_org_id is None:
        return "Warning: Organisation context required for knowledge retrieval."

    try:
        config = await get_platform_config()
        min_conf = config.get("rag_min_confidence", 20.0)
        max_res = config.get("rag_max_results", 5)

        docs = await _pgvector_search(
            query, 
            limit=max_res, 
            min_confidence=min_conf,
            organisation_id=resolved_org_id, 
            company_id=resolved_comp_id
        )
        logger.info("RAG search (min_conf=%s, limit=%s) found %d documents", min_conf, max_res, len(docs))
        if not docs:
            return "No relevant information found in the knowledge base."

        context = "\n\n".join([
            f"--- Source: {doc.source or 'KB'} | Crop: {doc.crop or '-'} | Problem: {doc.problem_type or '-'} ---\n"
            f"{doc.content}"
            for doc in docs
        ])
        return context
    except Exception as e:
        logger.error("RAG retrieval failed: %s", e, exc_info=True)
        return f"Retrieval error: {str(e)}"

@tool
async def diagnose_problem(query: str) -> str:
    """Find the crop disease, insects, or problems from expert PDF documents.
    Always use this tool when the user asks about crop issues or general agricultural information (like protein content).
    
    Args:
        query: Highly specific search query in English (e.g. 'soybean leaf yellowing symptoms')
    """
    logger.info("Chroma Diagnostic Search: %s", query)
    results = await chroma_service.query_diagnostics(query)
    if not results:
        return "No diagnostic information found in the expert documents."
    
    context = "\n\n".join([
        f"--- Document: {res['metadata'].get('source', 'Unknown')} | Confidence: {res['score']:.2f} ---\n{res['content']}"
        for res in results
    ])
    return context

@tool
async def suggest_products(problem: str, crop: str | None = None) -> str:
    """Use this tool to suggest actual products (seeds, pesticides, etc.) from the company database using smart search.
    ONLY use this during the ADVISORY stage after a diagnosis is confirmed.
    
    Args:
        problem: The diagnosed name of the disease/pest (e.g. 'Blast disease')
        crop: Optional crop name
    """
    logger.info("Product Advisory Search: problem=%r, crop=%r", problem, crop)
    
    query_text = f"{crop or ''} {problem}".strip()
    try:
        query_vector = await fetch_embedding(query_text)
    except Exception as e:
        logger.warning("Failed to fetch embedding for product search: %s", e)
        return "Error generating search query. Please try again."

    async with AsyncSessionLocal() as db:
        # Distance = 1 - CosineSimilarity
        distance_col = KnowledgeEntry.embedding.cosine_distance(query_vector)
        
        # Filter knowledge_entries for product sources
        stmt = (
            select(KnowledgeEntry)
            .where(KnowledgeEntry.source.like("product:%"))
            .order_by(distance_col)
            .limit(5)
        )
        
        result = await db.execute(stmt)
        entries = result.scalars().all()
        
    if not entries:
        return f"No specific products found for {problem} in {crop or 'this crop'}."
    
    advice = "Available Products:\n"
    for entry in entries:
        # KnowledgeEntry.content already contains a summarized product block
        advice += f"---\n{entry.content}\n"
    return advice
    
@tool
async def update_farmer_profile(
    name: str | None = None,
    village: str | None = None,
    district: str | None = None,
    state: str | None = None,
    crop_type: str | None = None,
    land_size: str | None = None,
    crop_area: str | None = None,
    problem_area: str | None = None,
    crop_age_days: str | None = None,
) -> str:
    """Use this tool IMMEDIATELY the moment you learn a new detail (name, village, land size, etc.).
    Do not wait for the end of the conversation.

    Args:
        name: Farmer's name
        village: Farmer's village
        district: Farmer's district
        state: Farmer's state
        crop_type: Name of the crop
        land_size: Total land size (e.g. "5 acres")
        crop_area: Area dedicated to this specific crop
        problem_area: Specific part of crop affected (e.g. "leaves", "roots")
        crop_age_days: Age of the crop in days
    """
    from services.voice.session_context import (
        get_current_phone_number,
        get_current_farmer_row_id,
        set_current_farmer_row_id,
        get_current_session_id,
        set_current_phone_number,
    )
    phone_number = get_current_phone_number()
    farmer_row_id = get_current_farmer_row_id()
    session_id = get_current_session_id()

    if not any([
        name, village, district, state, crop_type,
        land_size, crop_area, problem_area, crop_age_days
    ]):
        logger.warning("Ignoring empty update_farmer_profile tool call")
        return "Error: No profile fields were provided."
    
    if (not phone_number or farmer_row_id is None) and session_id:
        try:
            from db.models.call_session import CallSession
            async with AsyncSessionLocal() as db:
                call_row = (
                    await db.execute(
                        select(
                            CallSession.farmer_id,
                            CallSession.from_phone,
                            CallSession.phone_number,
                        ).where(CallSession.session_id == session_id)
                    )
                ).first()
                if call_row:
                    session_farmer_id, session_from_phone, session_phone = call_row
                    if farmer_row_id is None and session_farmer_id:
                        farmer_row_id = int(session_farmer_id)
                        set_current_farmer_row_id(farmer_row_id)
                    if not phone_number:
                        phone_number = session_from_phone or session_phone
                        if phone_number:
                            set_current_phone_number(phone_number)
        except Exception as e:
            logger.warning("Failed to resolve farmer context from call session: %s", e)

    if not phone_number and farmer_row_id is None:
        logger.warning("Attempted to update farmer profile without phone/farmer context")
        return "Error: No phone number associated with this session. Profile not updated."

    logger.info("Updating farmer profile for phone=%s: name=%r, village=%r, crop=%r",
                phone_number, name, village, crop_type)

    try:
        from db.models.farmer import Farmer
        from sqlalchemy import update, insert

        async with AsyncSessionLocal() as db:
            # Prepare values (filter out None)
            vals = {
                "name": name,
                "village": village,
                "district": district,
                "state": state,
                "crop_type": crop_type,
                "land_size": land_size,
                "crop_area": crop_area,
                "problem_area": problem_area,
                "crop_age_days": crop_age_days
            }
            update_vals = {k: v for k, v in vals.items() if v is not None}
            if farmer_row_id is None:
                # First profile write in this call: always create a new farmer row.
                insert_vals = {"phone_number": phone_number}
                insert_vals.update(update_vals)
                insert_stmt = insert(Farmer).values(**insert_vals).returning(Farmer.id)
                inserted_id = (await db.execute(insert_stmt)).scalar_one()
                set_current_farmer_row_id(inserted_id)
            else:
                # Subsequent writes in same call update only that call's row.
                if update_vals:
                    await db.execute(
                        update(Farmer)
                        .where(Farmer.id == farmer_row_id)
                        .values(**update_vals)
                    )

            await db.commit()
            
        return "Farmer profile successfully saved for this call."
    except Exception as e:
        logger.error("Failed to update farmer profile: %s", e, exc_info=True)
        return f"Error updating profile: {str(e)}"

@tool
async def end_call() -> str:
    """Use this tool IMMEDIATELY when the user says goodbye, namaste, hang up, "phone kaat do", "band kar raha hu", or explicitly ends the conversation.
    You MUST call this tool to physically drop the call. Do not just say goodbye without calling this tool.
    """
    logger.info("Agent invoked end_call tool.")
    from services.voice.session_context import get_current_session_id
    session_id = get_current_session_id()

    if session_id:
        try:
            from db.models.call_session import CallSession
            from sqlalchemy import update
            async with AsyncSessionLocal() as db:
                await db.execute(
                    update(CallSession)
                    .where(CallSession.session_id == session_id)
                    .values(status="completed")
                )
                await db.commit()
            logger.info("Call session %s marked as completed via agent end_call tool.", session_id)
        except Exception as e:
            logger.error("Failed to mark call session as completed: %s", e)

    return "Call ending sequence initiated. Say your final goodbye (e.g., 'Namaste')."


# ==========================================
# 4. Agent State & Prompts
# ==========================================
from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    stage: str # 'greeting', 'profiling', 'diagnostic', 'advisory'
    summary: str # Running summary of the conversation
    long_term_memory: str # Retrieved from vector DB
    farmer_profile: str # Persistent profile details from DB
    # Optimization 3: Cached router flags to avoid re-scanning all messages
    has_diagnosis: bool
    has_name_loc: bool
    has_crop: bool
    has_symptoms: bool


def _prepare_messages(state: AgentState, system_prompt: str, max_msgs: int = 8) -> list:
    """Optimization 1: Trim messages to a hard cap before LLM call.
    
    Keeps only the last `max_msgs` messages to prevent ever-growing token counts.
    Tool messages are kept intact since they carry essential context 
    (e.g., which profile fields were already saved).
    """
    all_msgs = list(state["messages"])
    # Keep only the last N messages
    recent = all_msgs[-max_msgs:] if len(all_msgs) > max_msgs else all_msgs
    return [SystemMessage(content=system_prompt)] + recent

LANGUAGE_MAP = {
    "hi": "Hindi (written entirely in Devanagari script / हिंदी)",
    "en": "English",
    "pa": "Punjabi (written entirely in Gurmukhi script / ਪੰਜਾਬੀ)",
    "mr": "Marathi (written entirely in Devanagari script / मराठी)"
}

def get_base_rules(language: str, summary: str = "", long_term_memory: str = "", farmer_profile: str = "") -> str:
    summary_block = f"\n\n--- PREVIOUS CONVERSATION CONTEXT ---\n{summary}\n--- END CONTEXT ---\n" if summary else ""
    memory_block = f"\n\n--- LONG-TERM MEMORY ABOUT THIS FARMER ---\n{long_term_memory}\n--- END LONG-TERM MEMORY ---\n" if long_term_memory else ""
    profile_block = f"\n\n--- FARMER PROFILE INFO (DO NOT ASK FOR THESE AGAIN) ---\n{farmer_profile}\n--- END FARMER PROFILE INFO ---\n" if farmer_profile else ""
    return f"""You are AI Krishi Sahayak (KisanVani), a friendly {language} female agricultural expert.{summary_block}{memory_block}{profile_block}
RULES:
- Speak feminine language.
- Be deeply empathetic. Acknowledge crop problems with genuine concern.
- You only have give information from retrieved content and if retrieved conent is irrelevant then you should politely decline and say you don't have the information (in {language}).
- STRICT FORMATTING: Speak ONLY in short spoken sentences. Do NOT use bullet points, bold text, markdown, or lists. ONLY plain text.
- Ask ONLY ONE short question at a time. Do not overwhelm the user.
- EXPERT RULE: You MUST use tools for any technical, diagnostic, or product-related questions. Do NOT answer from your internal knowledge if a tool is available.
- HANGUP RULE: If the user says goodbye, namaste, "phone kaat do", "band kar de raha hu", or implies they are hanging up, you MUST immediately use the `end_call` tool. Do not just output text, you MUST call the tool.
- If you receive "__USER_SILENCE__", ask if they can hear you (in {language}).
- If you receive "__USER_SILENCE_FINAL__", politely end the call (in {language}).
- CRITICAL LANGUAGE RULE: You MUST speak entirely in {language}. Translate any default Hindi examples or thoughts to {language} before responding.
"""

def get_greeting_prompt(language: str, summary: str = "", long_term_memory: str = "", farmer_profile: str = "") -> str:
    return get_base_rules(language, summary, long_term_memory, farmer_profile) + f"""
Current Stage: GREETING & CONSENT
When you receive "__CALL_STARTED__", greet the farmer warmly in {language}:
- Example (translate to {language} if needed): "Hello! I am your Agricultural Assistant from KisanVani. How can I help you today?"
- FLEXIBILITY RULE: If they ask a technical or diagnostic question immediately, USE THE `diagnose_problem` TOOL FIRST to answer them.
- After answering any digression, politely pivot back to profiling.
"""

def get_profiling_prompt(language: str, summary: str = "", long_term_memory: str = "", farmer_profile: str = "") -> str:
    return get_base_rules(language, summary, long_term_memory, farmer_profile) + f"""
Current Stage: FARMER PROFILING
Your primary goal is to learn their basic information to save in the database.
Gather these specific details naturally:
1. Name (`name`)
2. Location (`village`, `district`, `state`)
3. Total land size (`land_size`)
4. The crop they planted (`crop_type`)

MANDATORY TOOL RULE: Use `update_farmer_profile` tool IMMEDIATELY the moment you learn a new detail. Do not wait.
FLEXIBILITY RULE: If the farmer interrupts with a question about their crop, variety, or a disease, USE THE `diagnose_problem` TOOL IMMEDIATELY to answer them.
After answering, you MUST gently steer the conversation back to gathering their profile information.
"""

def get_diagnostic_prompt(language: str, summary: str = "", long_term_memory: str = "", farmer_profile: str = "") -> str:
    return get_base_rules(language, summary, long_term_memory, farmer_profile) + f"""
Current Stage: DIAGNOSTIC (CROP & PROBLEM IDENTIFICATION)
Be like a caring doctor trying to diagnose a patient's crop.

1. **PROACTIVE DIAGNOSIS**:
   - As soon as you know the crop name, use the `diagnose_problem` tool to find common diseases/pests for that crop in the expert documents.
   - Use the results to ask targeted questions.

2. **SYMBOLIC SYMPTOMS & FLEXIBILITY**:
   - Gather critical context: crop age, crop area, and problem area.
   - If they mention new profile details (like crop area), use `update_farmer_profile` immediately.

3. **MANDATORY TOOL RULE**:
   - If the user asks ANY question about crop diseases, pests, variety, or "how/why", you MUST use the `diagnose_problem` tool immediately. DO NOT answer from memory.

4. Do NOT suggest specific products yet.
5. After a successful diagnosis from the tool, reassure the farmer with concern.
"""

def get_advisory_prompt(language: str, summary: str = "", long_term_memory: str = "", farmer_profile: str = "") -> str:
    return get_base_rules(language, summary, long_term_memory, farmer_profile) + f"""
Current Stage: ADVISORY
You now understand the farmer's problem perfectly. 

1. **PRODUCT SEARCH**: Use the `suggest_products` tool to find actual products for the diagnosed problem.
2. **RECOMMENDATION**: Based ONLY on the retrieved product info, give clear recommendations. Do not list them out with numbers. Speak them naturally in a sentence.
3. **FLEXIBILITY**: If the farmer asks a general question, use the `diagnose_problem` tool to answer first, even if you are in the advisory stage.
4. **FALLBACK**: Only if no products OR diagnostic info are found, politely decline (in {language}).
5. **GATHER MISSING PROFILE INFO**: If you were forced to jump to this stage early, you MUST politely ask the user for their name or village if you haven't already. Use `update_farmer_profile` if they give it to you.
6. Close by asking if they need any other help.
"""

# ==========================================
# 5. Agent Factory (LangGraph)
# ==========================================
async def get_agent_executor(organisation_id: int | None = None, company_id: int | None = None):
    # Get current LLM provider from config for cache key
    try:
        config = await get_platform_config()
        llm_provider = config.get("llm_model", "groq")
    except Exception:
        llm_provider = "groq"

    cache_key = (organisation_id, company_id, llm_provider)
    if cache_key in _agent_cache:
        # Move to end to show it was recently used
        executor = _agent_cache.pop(cache_key)
        _agent_cache[cache_key] = executor
        return executor

    if checkpointer is None:
        await init_checkpointer()
    current_llm = await get_llm()

    # Define tools and wrappers
    if organisation_id is None:
        profiling_tools = [update_farmer_profile]
        diagnostic_tools = [update_farmer_profile, diagnose_problem]
        advisory_tools = [suggest_products, update_farmer_profile, end_call]
    else:
        _diagnose_problem_fn = diagnose_problem.coroutine
        _suggest_products_fn = suggest_products.coroutine
        _update_farmer_profile_fn = update_farmer_profile.coroutine
        _end_call_fn = end_call.coroutine

        @tool("end_call")
        async def end_call_scoped() -> str:
            """Send a signal to immediately hang up the phone call."""
            return await _end_call_fn()

        @tool("diagnose_problem")
        async def diagnose_problem_scoped(query: str) -> str:
            """Find crop disease or problem from expert PDF documents."""
            return await _diagnose_problem_fn(query=query)

        @tool("suggest_products")
        async def suggest_products_scoped(problem: str, crop: str | None = None) -> str:
            """Suggest products from the company database for the diagnosed problem."""
            return await _suggest_products_fn(problem=problem, crop=crop)
        
        @tool("update_farmer_profile")
        async def update_farmer_profile_scoped(
            name: str | None = None,
            village: str | None = None,
            district: str | None = None,
            state: str | None = None,
            crop_type: str | None = None,
            land_size: str | None = None,
            crop_area: str | None = None,
            problem_area: str | None = None,
            crop_age_days: str | None = None,
        ) -> str:
            """Update or create the farmer's profile in the database."""
            return await _update_farmer_profile_fn(
                name=name, village=village, district=district, state=state,
                crop_type=crop_type, land_size=land_size, crop_area=crop_area,
                problem_area=problem_area, crop_age_days=crop_age_days,
            )

        profiling_tools = [update_farmer_profile_scoped]
        diagnostic_tools = [update_farmer_profile_scoped, diagnose_problem_scoped]
        advisory_tools = [suggest_products_scoped, update_farmer_profile_scoped, end_call_scoped]

    # Extract unique tools into a dict for easy lookup
    all_staged_tools = profiling_tools + diagnostic_tools + advisory_tools 
    tools_by_name = {}
    for t in all_staged_tools:
        if getattr(t, "name", None):
            tools_by_name[t.name] = t

    # We still need a master list of unique tools for the ToolNode
    unique_tools = list(tools_by_name.values())

    # Intelligently bind tools to specific nodes to prevent state confusion
    # while allowing necessary digressions (using exact scoped functions directly where possible)
    if organisation_id is None:
        greeting_tools = [diagnose_problem]
        profiling_tools_bound = [update_farmer_profile, diagnose_problem]
        diagnostic_tools_bound = [diagnose_problem, update_farmer_profile]
        advisory_tools_bound = [suggest_products, diagnose_problem, update_farmer_profile, end_call]
    else:
        greeting_tools = [diagnose_problem_scoped]
        profiling_tools_bound = [update_farmer_profile_scoped, diagnose_problem_scoped]
        diagnostic_tools_bound = [diagnose_problem_scoped, update_farmer_profile_scoped]
        advisory_tools_bound = [suggest_products_scoped, diagnose_problem_scoped, update_farmer_profile_scoped, end_call_scoped]

    # The end_call tool is technically bound to advisory_tools_bound, but
    # it can also be added to greeting/profiling if the user says "hang up" early.
    greeting_tools.append(tools_by_name["end_call"])
    profiling_tools_bound.append(tools_by_name["end_call"])
    diagnostic_tools_bound.append(tools_by_name["end_call"])

    greeting_llm = current_llm.bind_tools(greeting_tools)
    profiling_llm = current_llm.bind_tools(profiling_tools_bound)
    diagnostic_llm = current_llm.bind_tools(diagnostic_tools_bound)
    advisory_llm = current_llm.bind_tools(advisory_tools_bound)

    # Node Functions — all use _prepare_messages for trimming + ToolMessage filtering
    async def greeting_node(state: AgentState, config: RunnableConfig):
        platform_config = await get_platform_config()
        lang_code = platform_config.get("default_language", "hi")
        lang_name = LANGUAGE_MAP.get(lang_code, "Hindi (Hinglish)")
        
        prompt = get_greeting_prompt(lang_name, state.get("summary", ""), state.get("long_term_memory", ""), state.get("farmer_profile", ""))
        messages = _prepare_messages(state, prompt)
        response = await greeting_llm.ainvoke(messages, config=config)
        return {"messages": [response], "stage": "greeting"}

    async def profiling_node(state: AgentState, config: RunnableConfig):
        platform_config = await get_platform_config()
        lang_code = platform_config.get("default_language", "hi")
        lang_name = LANGUAGE_MAP.get(lang_code, "Hindi (Hinglish)")

        prompt = get_profiling_prompt(lang_name, state.get("summary", ""), state.get("long_term_memory", ""), state.get("farmer_profile", ""))
        messages = _prepare_messages(state, prompt)
        response = await profiling_llm.ainvoke(messages, config=config)
        return {"messages": [response], "stage": "profiling"}

    async def diagnostic_node(state: AgentState, config: RunnableConfig):
        platform_config = await get_platform_config()
        lang_code = platform_config.get("default_language", "hi")
        lang_name = LANGUAGE_MAP.get(lang_code, "Hindi (Hinglish)")

        prompt = get_diagnostic_prompt(lang_name, state.get("summary", ""), state.get("long_term_memory", ""), state.get("farmer_profile", ""))
        messages = _prepare_messages(state, prompt)
        response = await diagnostic_llm.ainvoke(messages, config=config)
        return {"messages": [response], "stage": "diagnostic"}

    async def advisory_node(state: AgentState, config: RunnableConfig):
        platform_config = await get_platform_config()

        lang_code = platform_config.get("default_language", "hi")
        lang_name = LANGUAGE_MAP.get(lang_code, "Hindi (Hinglish)")

        prompt = get_advisory_prompt(lang_name, state.get("summary", ""), state.get("long_term_memory", ""), state.get("farmer_profile", ""))
        messages = _prepare_messages(state, prompt)
        response = await advisory_llm.ainvoke(messages, config=config)
        logger.info("Advisory node response: %s", response.content)
        return {"messages": [response], "stage": "advisory"}

    async def summarize_conversation_node(state: AgentState):
        """Summarize history when it gets too long."""
        summary = state.get("summary", "")
        if summary:
            summary_msg = f"This is summary of conversation to date: {summary}\n\n"
        else:
            summary_msg = ""
        
        # Take everything except the most recent 10 messages
        messages = state["messages"]
        messages_to_summarize = messages[:-10]
        
        from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
        
        # We need the LLM to process it (not streamed, fast background distillation)
        prompt = (
            f"{summary_msg}Extend this summary by taking into account the following new "
            "messages. Focus ONLY on actionable agricultural details: the farmer's name, location, "
            "crop type, crop age, and specific diseases/pests discussed. Ignore conversational filler."
        )
        # Use our current LLM to compress it
        messages_for_llm = [SystemMessage(content=prompt)] + list(messages_to_summarize)
        response = await current_llm.ainvoke(messages_for_llm)
        
        # Emit RemoveMessage objects so LangGraph permanently deletes them from memory
        delete_messages = [RemoveMessage(id=m.id) for m in messages_to_summarize]
        
        logger.info(f"Summarizer running. Compressed {len(messages_to_summarize)} messages into: {response.content}")
        
        from services.voice.session_context import get_current_phone_number
        phone_number = get_current_phone_number()
        if phone_number:
            await save_conversation_memory(phone_number, "memory", response.content)
            
        return {"summary": response.content, "messages": delete_messages}

    # Intelligent Router
    async def stage_router_node(state: AgentState):
        """Standard node that updates stage, fetches memory/profile in parallel."""
        decision = stage_router(state)
        logger.info(f"Deterministic router decision: {decision}")
        
        from services.voice.session_context import get_current_phone_number, get_current_farmer_row_id
        phone_number = get_current_phone_number()
        farmer_row_id = get_current_farmer_row_id()
        
        messages = state.get("messages", [])
        user_msg = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        user_text = user_msg.content.strip().lower() if user_msg else ""
        
        # Only search for non-trivial queries with enough context
        trivial_phrases = ["hello", "hi", "namaste", "ji", "haan", "nahi", "ok", "theek", "acha", "yes", "no", "thanks", "dhanyawad"]
        is_trivial = user_text in trivial_phrases or len(user_text.split()) <= 2
        
        # Optimization 2: Run memory search + farmer profile fetch in parallel
        async def _search_memory():
            if phone_number and user_text and not is_trivial:
                retrieved = await search_conversation_memory(phone_number, user_text)
                if retrieved:
                    logger.info(f"Retrieved long-term memory for phone {phone_number}")
                    return retrieved
            return state.get("long_term_memory", "")

        long_term_memory, farmer_profile = await asyncio.gather(
            _search_memory(),
            _fetch_farmer_profile(farmer_row_id)
        )

        # Update the state with stage, memory, and profile
        return {"stage": decision, "long_term_memory": long_term_memory, "farmer_profile": farmer_profile}

    def stage_router(state: AgentState) -> str:
        """Optimization 3: Use cached flags from state, fallback to scan only for new tool calls in the last message."""
        messages = state.get("messages", [])
        if not messages:
            return "greeting"

        # 1. Look for most recent human input for context
        user_msg = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        user_text = user_msg.content.lower() if user_msg else ""

        # 2. Start from cached flags (avoids re-scanning entire history)
        has_diagnosis = state.get("has_diagnosis", False)
        has_crop = state.get("has_crop", False)
        has_name_loc = state.get("has_name_loc", False)
        has_symptoms = state.get("has_symptoms", False)

        # Only scan the most recent messages for NEW tool calls (not the full history)
        scan_limit = min(len(messages), 6)  # Last 6 messages at most
        for msg in messages[-scan_limit:]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc["name"] == "update_farmer_profile":
                        args = tc.get("args") or tc.get("arguments") or {}
                        if args.get("name") and args.get("village"):
                            has_name_loc = True
                        if args.get("crop_type"):
                            has_crop = True
                        if args.get("problem_area") or args.get("crop_age_days"):
                            has_symptoms = True
                    if tc["name"] in ["diagnose_problem", "retrieve_context"]:
                        has_diagnosis = True

        # 3. Urgent Product Keywords Bypass
        product_keywords = ["dawai", "ilaj", "product", "medicine", "suggest", "konsa", "kaunsa", "konsi"]
        needs_product = any(word in user_text for word in product_keywords)
        
        if needs_product and has_diagnosis:
            logger.info("Urgent product keyword detected AND diagnosis complete. Bypassing to advisory.")
            return "advisory"
        elif needs_product and not has_diagnosis:
            logger.info("Urgent product keyword detected BUT diagnosis not complete. Routing to diagnostic.")
            return "diagnostic"

        # 4. Urgent Diagnostic Keywords (Bypass profiling, but MUST diagnose first)
        urgent_keywords = [
            "upay", "spray", "solution", "kya dalu", "kya karu",
            "protein", "variety", "bimari", "keeda", "keede", "pests", "yield", "pesticide",
            "insecticide", "fertilizer", "khad", "rog"
        ]
        if any(word in user_text for word in urgent_keywords):
            return "diagnostic"

        # 5. Initial Start
        if "__CALL_STARTED__" in user_text:
            return "greeting"

        # 6. Sequential Logic
        current_stage = state.get("stage", "greeting")
        
        logger.info(f"Router Debug: stage={current_stage}, has_diagnosis={has_diagnosis}, has_name_loc={has_name_loc}, has_crop={has_crop}, has_symptoms={has_symptoms}")
        
        # Deterministic stage transitions
        if current_stage == "greeting":
            if "__call_started__" in user_text:
                return "greeting"
            return "profiling"
            
        if current_stage == "profiling":
            if has_name_loc and has_crop:
                return "diagnostic"
            return "profiling"
            
        if current_stage == "diagnostic":
            if has_diagnosis:
                return "advisory"
            return "diagnostic"
            
        return current_stage

    # Build Graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("profiling", profiling_node)
    workflow.add_node("diagnostic", diagnostic_node)
    workflow.add_node("advisory", advisory_node)
    workflow.add_node("tools", ToolNode(unique_tools))
    workflow.add_node("summarize_conversation", summarize_conversation_node)

    # All nodes route back to the intelligent router after responding to user
    workflow.add_node("router", stage_router_node)
    
    workflow.add_edge(START, "router")
    
    def route_after_router(state: AgentState):
        return state.get("stage", "greeting")

    workflow.add_conditional_edges("router", route_after_router)

    def route_after_agent_or_tools(state: AgentState):
        """Should we summarize, or are we done/routing? Also caches tool flags."""
        messages = state.get("messages", [])
        last_msg = messages[-1] if messages else None
        
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            # Optimization 3: Update cached flags when tools are called
            for tc in last_msg.tool_calls:
                if tc["name"] == "update_farmer_profile":
                    args = tc.get("args") or tc.get("arguments") or {}
                    if args.get("name") and args.get("village"):
                        state["has_name_loc"] = True
                    if args.get("crop_type"):
                        state["has_crop"] = True
                    if args.get("problem_area") or args.get("crop_age_days"):
                        state["has_symptoms"] = True
                if tc["name"] in ["diagnose_problem", "retrieve_context"]:
                    state["has_diagnosis"] = True
            return "tools"
        
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
            # The agent has given a final text response. Turn is over.
            if len(messages) > 15:
                return "summarize_conversation"
            return END
            
        return "router"

    workflow.add_conditional_edges("greeting", route_after_agent_or_tools)
    workflow.add_conditional_edges("profiling", route_after_agent_or_tools)
    workflow.add_conditional_edges("diagnostic", route_after_agent_or_tools)
    workflow.add_conditional_edges("advisory", route_after_agent_or_tools)
    workflow.add_conditional_edges("tools", route_after_agent_or_tools)
    
    # After summarizing, the turn is over
    workflow.add_edge("summarize_conversation", END)

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.checkpoint.memory import MemorySaver
    
    cp_type = "None"
    if isinstance(checkpointer, AsyncPostgresSaver):
        cp_type = "AsyncPostgresSaver"
    elif isinstance(checkpointer, MemorySaver):
        cp_type = "MemorySaver"
        
    logger.info("Compiling graph with checkpointer type: %s", cp_type)
    executor = workflow.compile(checkpointer=checkpointer)
    _agent_cache[cache_key] = executor
    
    if len(_agent_cache) > MAX_AGENT_CACHE_SIZE:
        # popitem(last=False) removes the oldest key-value pair that was added/updated
        _agent_cache.popitem(last=False)
        
    return executor


# ==========================================
# 6. Session Management
# ==========================================
def create_session_id() -> str:
    return str(uuid.uuid4())


async def ask_agent(user_query: str, thread_id: str | None = None):
    """Utility to test the agent from terminal. Streams responses."""
    logger.info(f"USER QUERY: {user_query}")

    if thread_id is None:
        thread_id = create_session_id()

    config = {"configurable": {"thread_id": thread_id}}
    executor = await get_agent_executor()

    async for event in executor.astream(
        {"messages": [{"role": "user", "content": user_query}]},
        config=config,
        stream_mode="values",
    ):
        event["messages"][-1].pretty_print()
