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
from sqlalchemy import select

from db.base import AsyncSessionLocal
from db.models.knowledge_base import KnowledgeEntry
from services.voice.session_context import get_current_organisation_id, get_current_company_id
from services.config_service import get_platform_config

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
        model="llama-3.1-8b-instant",
        temperature=0.3,
        api_key=groq_api_key,
    )

def _create_openai_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
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
            logger.info("Using Groq (Llama 3.1) as LLM provider")
            return _create_groq_llm()
    except Exception as e:
        logger.error(f"Failed to get LLM from config, using default Groq: {e}")
        return _create_groq_llm()

openai_client = AsyncOpenAI(api_key=openai_api_key)

_agent_cache: dict[tuple[int | None, int | None], Any] = {}

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
    threshold: float = 0.4, # Default: 1 - 0.6 (60% confidence)
    organisation_id: int,
    company_id: int | None = None,
) -> list[KnowledgeEntry]:
    query_vector = await fetch_embedding(query)

    async with AsyncSessionLocal() as db:
        filters = [
            KnowledgeEntry.embedding.is_not(None),
            KnowledgeEntry.organisation_id == organisation_id,
            KnowledgeEntry.embedding.cosine_distance(query_vector) <= threshold
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


# ==========================================
# 3. Tools
# ==========================================
@tool
async def retrieve_context(query: str, organisation_id: int | None = None, company_id: int | None = None) -> str:
    """Search the agricultural knowledge base for crop problems, pest management,
    disease control, and advisory information. Use this tool when you have enough
    information about the farmer's problem to search for relevant advice.

    Args:
        query: Search query describing the crop problem, symptoms, or topic.
        organisation_id: Optional tenant scope ID.
        company_id: Optional sub-tenant company ID.
    """
    logger.info("RAG retrieval: query=%r org_id=%r company_id=%r", query, organisation_id, company_id)

    resolved_org_id = organisation_id
    if resolved_org_id is None:
        resolved_org_id = get_current_organisation_id()
    if resolved_org_id is None:
        env_org_id = os.getenv("VOICE_DEFAULT_ORGANISATION_ID")
        resolved_org_id = int(env_org_id) if env_org_id else None
        
    resolved_comp_id = company_id
    if resolved_comp_id is None:
        resolved_comp_id = get_current_company_id()

    if resolved_org_id is None:
        return "Warning: Organisation context required for knowledge retrieval."

    config = await get_platform_config()
    rag_limit = config.get("rag_max_results", 5)
    rag_min_conf = config.get("rag_min_confidence", 60)
    threshold = (100 - rag_min_conf) / 100.0

    try:
        docs = await _pgvector_search(query, limit=rag_limit, threshold=threshold, organisation_id=resolved_org_id, company_id=resolved_comp_id)
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
    """Update or create the farmer's profile in the database with information 
    gathered during the conversation. Use this tool as soon as you get any 
    personal or crop details from the farmer.

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


# ==========================================
# 4. Agent State & Prompts
# ==========================================
from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    stage: str # 'greeting', 'profiling', 'diagnostic', 'advisory'

BASE_RULES = """You are AI Krishi Sahayak (KisanVani), a friendly, highly empathetic female agricultural expert on a live phone call with an Indian farmer.
GENERAL RULES:
- Be deeply empathetic. If a farmer mentions crop damage or disease, express genuine concern first ("Arre, yeh toh badi pareshani ki baat hai", "Chinta mat kijiye, hum iska ilaj nikalenge").
- Keep sentences VERY SHORT and natural. The farmer is listening on a phone, not reading a text message.
- NEVER use formal terms. Use colloquial, empathetic language.
- NEVER use lists, bullet points, asterisks, or markdown. Output plain spoken text only.
- NEVER sound robotic. Use conversational fillers naturally.
- NEVER mention AI, database, tools, or technology. Act like a real human expert sitting in an advisory center.
- Ask ONLY ONE question at a time. Never interrogate the farmer.
"""

DEFAULT_RULES = """
LANGUAGE & TONE RULES:
- Speak ONLY in natural, conversational Hindi.
- Use feminine forms always: "main samajh sakti hoon", "main batati hoon".
- NEVER use English words (like 'spray', 'acre', 'tablet') if a common Hindi word exists (use 'छिड़काव', 'एकड़', 'दवाई').
- DO NOT mix English characters or alphabet into your response. Use ONLY Devanagari script.
- NEVER use Hinglish. The farmer expects pure, respectful Hindi.
"""

def _get_lang_rules(lang: str) -> str:
    if lang == "hi":
        return """
LANGUAGE & TONE RULES:
- शुद्ध और सरल हिंदी (Pure Hindi) का प्रयोग करें।
- "हिंग्लिश" (Hinglish) का प्रयोग बिल्कुल न करें। 
- अंग्रेजी शब्दों (जैसे 'doctor', 'problem', 'medicine') के स्थान पर हिंदी शब्दों ('डॉक्टर', 'परेशानी', 'दवाई') का प्रयोग करें, लेकिन उन्हें देवनागरी लिपि में ही लिखें।
- हमेशा स्त्रीलिंग (Feminine) का प्रयोग करें: "मैं समझ सकती हूँ", "मैं बताती हूँ"।
- वाक्य छोटे और स्पष्ट रखें ताकि फोन पर सुनने में आसानी हो।
"""
    if lang == "en":
        return """
LANGUAGE & TONE RULES:
- Speak ONLY in natural, conversational Indian English.
- Be deeply empathetic and polite.
- Keep sentences VERY SHORT for phone audio.
"""
    elif lang == "pa":
        return """
LANGUAGE & TONE RULES:
- Speak ONLY in natural, conversational Punjabi.
- Use feminine forms always.
- Be deeply empathetic and polite.
"""
    elif lang == "mr":
        return """
LANGUAGE & TONE RULES:
- Speak ONLY in natural, conversational Marathi.
- Use feminine forms always.
- Be deeply empathetic and polite.
"""
    return DEFAULT_RULES

def _get_greeting(lang: str) -> str:
    greetings = {
        "hi": '- "नमस्ते! मैं किसानवाणी से आपकी कृषि सहायक बोल रही हूँ। आशा है आप ठीक होंगे। यह कॉल रिकॉर्ड की जा रही है। बताइए, आज मैं आपकी क्या मदद कर सकती हूँ?"',
        "en": '- "Hello! I am your Krishi Sahayak from KisanVani. I hope you are doing well. (This call is being recorded for quality purposes). How can I help you today?"',
        "pa": '- "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਕਿਸਾਨਵਾਣੀ ਤੋਂ ਤੁਹਾਡੀ ਕ੍ਰਿਸ਼ੀ सਹਾਇਕ ਬੋਲ ਰਹੀ ਹਾਂ। ਉਮੀਦ ਹੈ ਕਿ ਤੁਸੀਂ ਠੀਕ ਹੋਵੋਗੇ। (ਇਹ ਕਾਲ ਕੁਆਲਿਟੀ ਲਈ ਰਿਕਾਰਡ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ)। ਦੱਸੋ, ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦੀ ਹਾਂ?"',
        "mr": '- "नमस्कार! मी किसानवाणीकडून आपली कृषी सहाय्यक बोलत आहे. आशा आहे की आपण ठीक असाल. (हा कॉल गुणवत्तेसाठी रेकॉर्ड केला जात आहे). सांगा, आज मी आपली काय मदत करू शकते?"'
    }
    return greetings.get(lang, greetings["hi"])

def _get_name_ask(lang: str) -> str:
    prompts = {
        "hi": '"जब तक आप बताते हैं, क्या मैं आपका शुभ नाम जान सकती हूँ?"',
        "en": '"While you tell me that, may I know your name please?"',
        "pa": '"ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਦੱਸਦੇ ਹੋ, ਕੀ ਮੈਂ ਤੁਹਾਡਾ ਸ਼ੁਭ ਨਾਮ ਜਾਣ ਸਕਦੀ ਹਾਂ?"',
        "mr": '"तुम्ही सांगेपर्यंत, मी तुमचे नाव जाणून घेऊ शकते का?"'
    }
    return prompts.get(lang, prompts["hi"])

HANGUP_RULES = """
CALL TERMINATION RULE:
- If the conversation has reached a natural end (e.g., the farmer says "Thank you", or "Theek hai, dhanyawad"), greet them one last time and append the marker "[END_CALL]" at the VERY END of your response.
- Example: "Theek hai, apna khayal rakhiyega. Namaste! [END_CALL]"

SILENCE HANDLING:
- If you receive "__USER_SILENCE__", say ONLY: "Hello, kya aap mujhe sun pa rahe hain? Aap wahan hain?"
- If you receive "__USER_SILENCE_FINAL__", say ONLY: "Lagta hai aapki aawaz nahi aa rahi hai. Main call kaat rahi hoon. Aap fursat mein phir se call kar lijiyega. Namaste! [END_CALL]"
"""

GREETING_PROMPT = """
Current Stage: GREETING & CONSENT
When you receive "__CALL_STARTED__", greet the farmer warmly:
{greeting_text}
- Do NOT force them to explicitly say "yes" to recording unless they object.
- If they ask a question immediately, answer it. Otherwise, politely ask for their name: {name_ask_text}
"""

PROFILING_PROMPT = BASE_RULES + """
Current Stage: FARMER PROFILING
Your goal is to learn their basic information to save in the database (`update_farmer_profile` tool).
Gather these specific details naturally, WITHOUT sounding like an interrogator:
1. Name (`name`)
2. Location (`village`, `district`, `state`)
3. Total land size (`land_size`)
4. The crop they planted (`crop_type`)

- If they tell you their problem, acknowledge it FIRST, then gently ask for the missing profile details (e.g. location or land size).
- Use the `update_farmer_profile` tool IMMEDIATELY when you learn a new detail.
- Once you know these basic details, gently steer to the specific crop problem.
"""

DIAGNOSTIC_PROMPT = BASE_RULES + """
Current Stage: DIAGNOSTIC (CROP & PROBLEM IDENTIFICATION)
Be like a caring doctor trying to diagnose a patient.
You must gather information SPECIFICALLY for the database columns using the `update_farmer_profile` tool:
1. The area planted for this specific crop (`crop_area`)
2. Crop age or duration (`crop_age_days`)
3. The specific part of the crop affected or symptoms (`problem_area`)

Rules for questioning:
- ONLY ask questions to fill out `crop_area`, `crop_age_days`, and `problem_area`. DO NOT ask unknown or irrelevant questions.
- Don't ask a new question before acknowledging their previous answer.
- Gather details one by one conversationally.

CRITICAL RULE: DO NOT SUGGEST ANY CHEMICALS, MEDICINES, OR TREATMENTS YET. Even if you know the answer, you are FORBIDDEN from naming products from your own knowledge.

Use the `update_farmer_profile` tool IMMEDIATELY to save `crop_age_days`, `crop_area`, or `problem_area` as you learn them.
Once the diagnostic fields are collected and the farmer asks for medicine/advice, reassure them and let the router transition you to the advisory stage by saying something like: "Aap chinta mat kijiye, main turant check karke iska sabse accha ilaj batati hoon."
"""

ADVISORY_PROMPT = BASE_RULES + """
Current Stage: ADVISORY
You now understand the farmer's problem perfectly. 
1. If you haven't yet, you MUST use the `retrieve_context` tool with a search query combining: crop + symptoms. DO NOT provide any advice until you have run this tool.
2. Based ONLY on the retrieved context, weave the advice into a caring, human response.
3. Cover the necessary steps securely:
   - "Abhi kya karein" (Immediate action)
   - "Aage kya dhyan rakhein" (Future prevention)

CRITICAL RULE: NEVER INVENT OR GUESS PRODUCT NAMES. If the tool returns NO information, you MUST say: "Maaf kijiyega, mere paas iski satik dawai abhi nahi hai, main aapko ek krishi expert se baat karwa sakti hoon"

4. After giving the advice, wait for their response or gently ask, "Kya iske ilawa bhi fasal mein koi aur pareshani aa rahi hai?"
If they are satisfied and have no more questions, close with a warm, encouraging goodbye.
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
        return _agent_cache[cache_key]

    if checkpointer is None:
        await init_checkpointer()
    current_llm = await get_llm()

    # Define tools and wrappers
    if organisation_id is None:
        profiling_tools = [update_farmer_profile]
        advisory_tools = [retrieve_context]
        _retrieve_context_direct = retrieve_context.coroutine
    else:
        _retrieve_context_fn = retrieve_context.coroutine
        _update_farmer_profile_fn = update_farmer_profile.coroutine

        @tool("retrieve_context")
        async def retrieve_context_scoped(query: str) -> str:
            """Search agricultural knowledge base for this organisation's crop advisory data."""
            return await _retrieve_context_fn(query=query, organisation_id=organisation_id, company_id=company_id)

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
            """Update or create the farmer's profile in the database with information gathered during the conversation."""
            return await _update_farmer_profile_fn(
                name=name, village=village, district=district, state=state,
                crop_type=crop_type, land_size=land_size, crop_area=crop_area,
                problem_area=problem_area, crop_age_days=crop_age_days,
            )

        profiling_tools = [update_farmer_profile_scoped]
        advisory_tools = [retrieve_context_scoped]
        _retrieve_context_direct = retrieve_context_scoped.coroutine

    def _recent_has_retrieval(messages: Sequence[BaseMessage], lookback: int = 12) -> bool:
        """Check whether recent state already includes KB retrieval output."""
        for msg in reversed(list(messages)[-lookback:]):
            if getattr(msg, "type", "") != "tool":
                continue
            if getattr(msg, "name", "") == "retrieve_context":
                return True
            content = str(getattr(msg, "content", "") or "").lower()
            if "source:" in content or "no relevant information found in the knowledge base" in content:
                return True
        return False

    def _build_retrieval_query(messages: Sequence[BaseMessage]) -> str:
        """Build a compact crop/symptom query from recent farmer utterances."""
        human_texts: list[str] = []
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                txt = str(getattr(msg, "content", "") or "").strip()
                if txt and not txt.startswith("__"):
                    human_texts.append(txt)
            if len(human_texts) >= 4:
                break

        query = " ".join(reversed(human_texts))
        query = re.sub(r"\s+", " ", query).strip()
        return query or "crop symptoms and treatment"

    # Initialize node LLMs
    # Keep both tools available after greeting so stage transitions do not block
    # legitimate tool usage in mixed user utterances (profile + advisory together).
    all_tools = profiling_tools + advisory_tools
    greeting_llm = current_llm.bind_tools([])
    profiling_llm = current_llm.bind_tools(all_tools)
    diagnostic_llm = current_llm.bind_tools(all_tools)
    advisory_llm = current_llm.bind_tools(all_tools)

    # Node Functions
    async def greeting_node(state: AgentState):
        config = await get_platform_config()
        lang = config.get("default_language", "hi")
        
        lang_rules = _get_lang_rules(lang)
        prompt = BASE_RULES + lang_rules + GREETING_PROMPT.format(
            greeting_text=_get_greeting(lang),
            name_ask_text=_get_name_ask(lang)
        ) + HANGUP_RULES
        
        messages = [SystemMessage(content=prompt)] + list(state["messages"])
        response = await greeting_llm.ainvoke(messages)
        return {"messages": [response], "stage": "greeting"}

    async def profiling_node(state: AgentState):
        config = await get_platform_config()
        lang = config.get("default_language", "hi")
        prompt = BASE_RULES + _get_lang_rules(lang) + PROFILING_PROMPT + HANGUP_RULES
        
        messages = [SystemMessage(content=prompt)] + list(state["messages"])
        response = await profiling_llm.ainvoke(messages)
        return {"messages": [response], "stage": "profiling"}

    async def diagnostic_node(state: AgentState):
        config = await get_platform_config()
        lang = config.get("default_language", "hi")
        prompt = BASE_RULES + _get_lang_rules(lang) + DIAGNOSTIC_PROMPT + HANGUP_RULES
        
        messages = [SystemMessage(content=prompt)] + list(state["messages"])
        response = await diagnostic_llm.ainvoke(messages)
        return {"messages": [response], "stage": "diagnostic"}

    async def advisory_node(state: AgentState):
        raw_messages = list(state["messages"])

        config = await get_platform_config()
        lang = config.get("default_language", "hi")
        force_kb = config.get("force_kb_approval", True)
        strictness = config.get("rag_strictness_level", "medium")
        lang_rules = _get_lang_rules(lang)

        # Hard guard: do not allow advisory to proceed without KB retrieval.
        if not _recent_has_retrieval(raw_messages):
            forced_query = _build_retrieval_query(raw_messages)
            logger.info("Forcing retrieve_context before advisory response: query=%r", forced_query)
            kb_context = await _retrieve_context_direct(query=forced_query)

            if (
                "No relevant information found in the knowledge base." in kb_context
                or kb_context.startswith("Retrieval error:")
                or kb_context.startswith("Warning: Organisation context required")
            ):
                if force_kb:
                    content = "माफ कीजियेगा, मेरे पास इसकी सटीक दवाई अभी नहीं है, मैं आपको एक कृषि विशेषज्ञ से बात करवा सकती हूँ।"
                    if lang == "en": content = "I'm sorry, I don't have the exact medicine for this right now, I can connect you with an agricultural expert."
                    elif lang == "pa": content = "ਮਾਫ ਕਰਨਾ, ਮੇਰੇ ਕੋਲ ਇਸ ਲਈ ਸਹੀ ਦਵਾਈ ਨਹੀਂ ਹੈ, ਮੈਂ ਤੁਹਾਨੂੰ ਇੱਕ ਖੇਤੀਬਾੜੀ ਮਾਹਿਰ ਨਾਲ ਜੋੜ ਸਕਦਾ ਹਾਂ।"
                    elif lang == "mr": content = "क्षमस्व, माझ्याकडे सध्या यासाठी अचूक औषध नाही, मी तुम्हाला कृषी तज्ञाशी जोडून देऊ शकते."
                    
                    return {
                        "messages": [AIMessage(content=content)],
                        "stage": "advisory",
                    }
                else:
                    logger.info("KB match empty but force_kb_approval is False. Allowing general response.")
                    # Allow LLM to proceed without KB grounding
                    prompt = BASE_RULES + lang_rules + ADVISORY_PROMPT + HANGUP_RULES
                    messages = [SystemMessage(content=prompt)] + raw_messages
                    response = await advisory_llm.ainvoke(messages)
                    return {"messages": [response], "stage": "advisory"}

            grounding_prompt = (
                BASE_RULES + lang_rules + ADVISORY_PROMPT + HANGUP_RULES
                + f"\n\nSTRICT GROUNDING RULE (Strictness: {strictness}):\nUse ONLY this retrieved context. If details are missing, do not guess medicines.\n\n"
                + kb_context
            )
            response = await advisory_llm.ainvoke([SystemMessage(content=grounding_prompt)] + raw_messages)
            return {"messages": [response], "stage": "advisory"}

        messages = [SystemMessage(content=ADVISORY_PROMPT)] + raw_messages
        response = await advisory_llm.ainvoke(messages)
        return {"messages": [response], "stage": "advisory"}

    # Intelligent Router (LLM decides when to switch stages)
    # This prevents edge case routing bugs
    async def stage_router(state: AgentState) -> str:
        messages = state["messages"]
        last_msg = messages[-1] if messages else None
        
        # Always handle tool calls natively
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        if getattr(last_msg, "type", "") == "tool":
            return state.get("stage", "greeting")

        # Emergency override: If the user explicitly asks for medicine, advice, or treatment, force ADVISORY stage
        if isinstance(last_msg, HumanMessage):
            user_text = last_msg.content.lower()
            if any(word in user_text for word in ["dawai", "ilaj", "kya karun", "kya dalu", "medicine", "spray"]):
                return "advisory"

        # Routing decision based on conversation analysis
        router_prompt = """You are a strict conversation router for an agricultural AI. Analyze the conversation history.
Rule 1: If the farmer just called, return 'greeting'.
Rule 2: If the AI is asking for name/location, return 'profiling'.
Rule 3: If the AI is asking about crop symptoms, duration, or area, return 'diagnostic'.
Rule 4: If the farmer has stated their symptoms AND is now waiting for a solution/medicine, you MUST return 'advisory'.
Return ONLY ONE word: 'greeting', 'profiling', 'diagnostic', or 'advisory'."""

        router_sys = SystemMessage(content=router_prompt)
        
        # Filter out tool-related messages to avoid OpenAI BadRequestError (code 400)
        chat_history_for_router = []
        for m in messages:
            if getattr(m, "type", "") == "tool":
                continue
            if hasattr(m, "tool_calls") and m.tool_calls:
                continue
            if getattr(m, "content", ""):
                chat_history_for_router.append(m)

        try:
            route_decision = await current_llm.ainvoke([router_sys] + chat_history_for_router[-5:]) # Look at recent text context
            choice = route_decision.content.strip().lower()
            if "advisory" in choice: return "advisory"
            if "diagnostic" in choice: return "diagnostic"
            if "profiling" in choice: return "profiling"
            return "greeting"
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return state.get("stage", "greeting") # Fallback to current stage

    # Build Graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("profiling", profiling_node)
    workflow.add_node("diagnostic", diagnostic_node)
    workflow.add_node("advisory", advisory_node)
    workflow.add_node("tools", ToolNode(all_tools))

    # All nodes route back to the intelligent router after responding to user
    workflow.add_conditional_edges(START, stage_router)
    
    def route_after_agent(state: AgentState):
        messages = state.get("messages", [])
        last_msg = messages[-1] if messages else None
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges("greeting", route_after_agent)
    workflow.add_conditional_edges("profiling", route_after_agent)
    workflow.add_conditional_edges("diagnostic", route_after_agent)
    workflow.add_conditional_edges("advisory", route_after_agent)
    
    # Tool edge
    workflow.add_conditional_edges("tools", lambda state: state.get("stage", "greeting"))

    executor = workflow.compile(checkpointer=checkpointer)
    _agent_cache[cache_key] = executor
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
