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

BASE_RULES = """You are AI Krishi Sahayak (KisanVani), a friendly Hinglish female agricultural expert.
RULES:
- Speak feminine Hinglish (Hindi + English words like 'spray', 'dawai').
- deeply empathetic. Acknowledge crop problems with concern.
- SHORT spoken sentences. No lists or markdown. Plain text only.
- Ask ONLY ONE question at a time.
- If you receive "__USER_SILENCE__", say: "Hello, kya aap mujhe sun pa rahe hain?"
- If you receive "__USER_SILENCE_FINAL__", say: "Aapki aawaz nahi aa rahi hai. Main call kaat rahi hoon. Namaste!"
"""

GREETING_PROMPT = BASE_RULES + """
Current Stage: GREETING & CONSENT
When you receive "__CALL_STARTED__", greet the farmer warmly:
- "Namaste! Main KisanVani se, aapki Krishi Sahayak bol rahi hoon. Asha karti hoon aap theek honge. (Yeh call quality ke liye record ho rahi hai). Boliye, aaj main aapki kya madad kar sakti hoon?"
- Do NOT force them to explicitly say "yes" to recording unless they object.
- If they ask a question immediately, answer it. Otherwise, politely ask for their name: "Jab tak aap batate hain, kya main aapka shubh naam jaan sakti hoon?"
"""

PROFILING_PROMPT = BASE_RULES + """
Current Stage: FARMER PROFILING
MANDATORY TOOL RULE: Use `update_farmer_profile` tool IMMEDIATELY the moment you learn a new detail (name, village, etc.). DO NOT wait!

Your goal is to learn their basic information to save in the database.
Gather these specific details naturally:
1. Name (`name`)
2. Location (`village`, `district`, `state`)
3. Total land size (`land_size`)
4. The crop they planted (`crop_type`)

- If they tell you their problem, acknowledge it FIRST, then gently ask for the missing profile details (e.g. location or land size).
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

MANDATORY: You MUST call `retrieve_context` before giving any advice. DO NOT rely on your own knowledge for product names or dosages.
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
        return query or "crop disease symptoms treatment"

    # Initialize node LLMs with stage-specific tools
    greeting_llm = current_llm.bind_tools([])
    profiling_llm = current_llm.bind_tools(profiling_tools)
    diagnostic_llm = current_llm.bind_tools(profiling_tools)
    advisory_llm = current_llm.bind_tools(advisory_tools)
    all_tools = profiling_tools + advisory_tools

    # Node Functions
    async def greeting_node(state: AgentState):
        config = await get_platform_config()
        lang = config.get("default_language", "hi")
        lang_instr = f"\nUSER LANGUAGE: {lang}. Respond in this language strictly."
        
        messages = [SystemMessage(content=GREETING_PROMPT + lang_instr)] + list(state["messages"])
        response = await greeting_llm.ainvoke(messages)
        return {"messages": [response], "stage": "greeting"}

    async def profiling_node(state: AgentState):
        config = await get_platform_config()
        lang = config.get("default_language", "hi")
        lang_instr = f"\nUSER LANGUAGE: {lang}. Respond in this language strictly."

        messages = [SystemMessage(content=PROFILING_PROMPT + lang_instr)] + list(state["messages"])
        response = await profiling_llm.ainvoke(messages)
        return {"messages": [response], "stage": "profiling"}

    async def diagnostic_node(state: AgentState):
        config = await get_platform_config()
        lang = config.get("default_language", "hi")
        lang_instr = f"\nUSER LANGUAGE: {lang}. Respond in this language strictly."

        messages = [SystemMessage(content=DIAGNOSTIC_PROMPT + lang_instr)] + list(state["messages"])
        response = await diagnostic_llm.ainvoke(messages)
        return {"messages": [response], "stage": "diagnostic"}

    async def advisory_node(state: AgentState):
        config = await get_platform_config()
        force_kb = config.get("force_kb_approval", True)

        if force_kb and not _recent_has_retrieval(state["messages"]):
            forced_query = _build_retrieval_query(state["messages"])
            logger.info("Hard guard: Forcing retrieve_context before advisory (force_kb_approval=True): %r", forced_query)
            return {
                "messages": [AIMessage(
                    content="Ji, main abhi check karke batati hoon...",
                    tool_calls=[{
                        "name": "retrieve_context",
                        "args": {"query": forced_query},
                        "id": f"call_{uuid.uuid4().hex[:12]}"
                    }]
                )],
                "stage": "advisory"
            }

        lang = config.get("default_language", "hi")
        lang_instr = f"\nUSER LANGUAGE: {lang}. Respond in this language strictly."

        messages = [SystemMessage(content=ADVISORY_PROMPT + lang_instr)] + list(state["messages"])
        response = await advisory_llm.ainvoke(messages)
        logger.info("Advisory node response: %s", response.content)
        return {"messages": [response], "stage": "advisory"}

    # Intelligent Router (LLM decides when to switch stages)
    async def stage_router_node(state: AgentState):
        """Standard node that simply updates the stage in state."""
        decision = stage_router(state)
        logger.info(f"Deterministic router decision: {decision}")
        return {"stage": decision}

    def stage_router(state: AgentState) -> str:
        messages = state.get("messages", [])
        if not messages:
            return "greeting"

        # 1. Look for most recent human input for context
        user_msg = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
        user_text = user_msg.content.lower() if user_msg else ""

        # 2. Emergency Keywords (Immediate leap to advisory)
        advisory_keywords = ["dawai", "ilaj", "upay", "medicine", "spray", "solution", "kya dalu", "kya karu"]
        if any(word in user_text for word in advisory_keywords):
            return "advisory"

        # 3. Initial Start
        if "__CALL_STARTED__" in user_text:
            return "greeting"

        # 4. Sequential Logic
        current_stage = state.get("stage", "greeting")
        
        # Heuristic markers from history
        has_name_loc = False
        has_symptoms = False
        
        # Look back to see what we've accomplished
        msg_debug = []
        for msg in messages: # Look at all messages to ensure we don't forget stages
            # Get type and tool call info for logging
            m_type = type(msg).__name__
            t_calls = getattr(msg, "tool_calls", [])
            tc_names = [tc.get("name") for tc in t_calls] if t_calls else []
            msg_debug.append(f"{m_type}(tools={tc_names})")

            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc["name"] == "update_farmer_profile":
                        args = tc.get("args") or tc.get("arguments") or {}
                        if args.get("name") or args.get("village"):
                            has_name_loc = True
                        if args.get("problem_area") or args.get("crop_age_days"):
                            has_symptoms = True
        
        logger.info(f"Router Debug: stage={current_stage}, has_name_loc={has_name_loc}, has_symptoms={has_symptoms}, history_types={msg_debug}")
        
        if current_stage == "greeting":
            if "__call_started__" in user_text:
                return "greeting"
            return "profiling"
            
        if current_stage == "profiling":
            if has_name_loc and has_symptoms: return "advisory"
            if has_name_loc: return "diagnostic"
            if has_symptoms: return "diagnostic" # Move to diagnostic if symptoms but no location
            return "profiling"
            
        if current_stage == "diagnostic":
            if has_symptoms: return "advisory"
            return "diagnostic"
            
        return current_stage

    # Build Graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("profiling", profiling_node)
    workflow.add_node("diagnostic", diagnostic_node)
    workflow.add_node("advisory", advisory_node)
    workflow.add_node("tools", ToolNode(all_tools))

    # All nodes route back to the intelligent router after responding to user
    workflow.add_node("router", stage_router_node)
    
    workflow.add_edge(START, "router")
    
    def route_after_router(state: AgentState):
        return state.get("stage", "greeting")

    workflow.add_conditional_edges("router", route_after_router)
    
    def route_after_agent(state: AgentState):
        messages = state.get("messages", [])
        last_msg = messages[-1] if messages else None
        
        logger.info("Last AI message tool calls: %s", getattr(last_msg, "tool_calls", None))

        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        
        # If the LLM didn't call a tool but just learned something, 
        # we might want to re-route instantly, but for voice we usually END.
        # But per user request: "Change return END to return stage_router(state)"
        # We return to router to allow another node to run if needed.
        # SAFETY: If the last message was a text response from the agent, 
        # we should probably END the turn to avoid the AI talking to itself.
        # We'll use a simple heuristic: if it was a plain AIMessage without tool calls, END.
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
            return END
            
        return "router"

    workflow.add_conditional_edges("greeting", route_after_agent)
    workflow.add_conditional_edges("profiling", route_after_agent)
    workflow.add_conditional_edges("diagnostic", route_after_agent)
    workflow.add_conditional_edges("advisory", route_after_agent)
    
    # Tool edge loops back to the router to decide the next stage
    workflow.add_edge("tools", "router")

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
