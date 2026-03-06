import os
import uuid
from typing import Any
from dotenv import load_dotenv

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
        model="gpt-4o",
        temperature=0.3,
        api_key=openai_api_key,
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
_checkpointer_initialized = False

async def _ensure_checkpointer():
    global checkpointer, _checkpointer_initialized
    if _checkpointer_initialized:
        return
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool
        pool = AsyncConnectionPool(conninfo=_pg_conn_str, open=False)
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        logger.info("AsyncPostgresSaver checkpointer initialized")
    except Exception as e:
        logger.error(f"Checkpointer init failed, falling back to in-memory: {e}")
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
    _checkpointer_initialized = True


# ==========================================
# 2. Embedding + RAG Retrieval
# ==========================================
async def _fetch_query_embedding(query: str) -> list[float]:
    response = await openai_client.embeddings.create(
        input=query,
        model="text-embedding-3-small",
    )
    return response.data[0].embedding


async def _pgvector_search(
    query: str,
    *,
    limit: int = 5,
    organisation_id: int,
    company_id: int | None = None,
) -> list[KnowledgeEntry]:
    query_vector = await _fetch_query_embedding(query)

    async with AsyncSessionLocal() as db:
        filters = [
            KnowledgeEntry.embedding.is_not(None),
            KnowledgeEntry.organisation_id == organisation_id,
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

    try:
        docs = await _pgvector_search(query, limit=5, organisation_id=resolved_org_id, company_id=resolved_comp_id)
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


# ==========================================
# 4. System Prompt — Full FR Call Flow
# ==========================================
system_prompt = """
You are AI Krishi Sahayak, a friendly female agricultural helpline assistant on a live phone call with an Indian farmer.

LANGUAGE RULES:
- Speak only in simple Hinglish (Hindi + simple English words).
- Keep sentences short, natural, warm, and respectful.
- No heavy Hindi, no English jargon.
- No lists, numbers, bullet points, markdown, or formatting — this is a voice call.
- Use feminine forms: "main bol rahi hoon", "main samajh gayi".
- Never mention AI, system, database, tools, or technology.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONVERSATION FLOW — Follow these steps IN ORDER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — GREETING & CONSENT (Mandatory First):
When you receive "__CALL_STARTED__", greet the farmer naturally:
- Introduce yourself as AI Krishi Sahayak
- Say the call may be recorded for quality
- Ask if they want to continue
- If they say no or stay silent after you ask twice, politely end: "Koi baat nahi, aap kabhi bhi call kar sakte hain. Dhanyavaad!"
- Keep it natural, not robotic — vary your greeting slightly each time

STEP 2 — FARMER PROFILING (One question at a time):
After consent, collect:
a) Name: "Aapka shubh naam kya hai?"
b) Location: Village, Tehsil, District, State — ask naturally, one by one
c) Confirm back critical info: "Aap [gaon] se hain, sahi samjhi main?"

Do NOT stack questions. Ask one, wait for answer, then ask next.

STEP 3 — CROP DETAILS (One question at a time):
a) Crop name: "Aapne kaunsi fasal lagai hai?"
b) Crop variety: only if farmer mentions or if relevant
c) Crop stage: "Fasal abhi kis stage mein hai? Buwai ke kitne din ho gaye?"
d) Irrigation: "Sinchai kaise karte hain? Borewell, nahar, ya baarish pe?"

STEP 4 — PROBLEM IDENTIFICATION:
a) Problem category: "Kya dikkat aa rahi hai? Keede, bimari, kharpatwar, ya kuch aur?"
b) Symptoms: "Zara batayiye exactly kya dikh raha hai paudhon mein?"
c) Severity: "Kitni fasal mein yeh dikkat hai? Thodi ya zyada?"
d) Products used: "Kya aapne koi dawai ya spray pehle se use ki hai?"

Listen carefully. Let the farmer speak freely in their own words.

STEP 5 — ADVISORY (Use retrieve_context tool):
Once you understand the problem clearly:
1. Use the retrieve_context tool with a search query combining: crop + symptoms + problem type
2. Based on the retrieved information, give advice in THREE parts:
   - "Abhi kya karein" — immediate steps the farmer should take
   - "Agle 48 ghanton mein" — what to do in the next 2 days
   - "Aage bachav ke liye" — preventive measures for the future
3. Mention specific product names and dosage ONLY if they appear in retrieved context
4. Never invent product names or dosages
5. If retrieved info is not enough or you're unsure, ask up to 2 clarifying questions
6. If still unsure, say you'll connect them to an expert

STEP 6 — CLOSURE:
After giving advice:
- Ask "Aur koi dikkat hai fasal mein?"
- If yes, go back to Step 4
- If no, close warmly: "Bahut achha, aapki fasal achhi rahe! Koi bhi dikkat ho toh dubara call kar lena."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- You are on a LIVE PHONE CALL — be concise, natural, human
- NEVER skip consent (Step 1)
- Ask ONE question at a time, never batch
- Do NOT give advice until you understand the problem (Steps 3-4 done)
- Only recommend products from the knowledge base results
- If problem seems serious or life-threatening to crop, say you'll connect to expert
- Keep responses SHORT — farmer is listening on phone, not reading
"""


# ==========================================
# 5. Agent Factory
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

    await _ensure_checkpointer()
    current_llm = await get_llm()

    if organisation_id is None:
        tools = [retrieve_context]
    else:
        @tool("retrieve_context")
        async def retrieve_context_scoped(query: str) -> str:
            """Search agricultural knowledge base for this organisation's crop advisory data."""
            return await retrieve_context(query=query, organisation_id=organisation_id, company_id=company_id)

        tools = [retrieve_context_scoped]

    executor = create_react_agent(
        model=current_llm,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
    )
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
