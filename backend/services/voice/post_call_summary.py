import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import select

from db.base import AsyncSessionLocal
from db.models.call_session import CallSession
from db.models.call_summary import CallSummary
from db.models.call_metrics import CallMetrics, CallOutcome

# Using Groq/OpenAI/Gemini based on platform config natively
from services.voice.llm import get_llm, get_agent_executor

logger = logging.getLogger(__name__)

class CallSummaryMetricsPayload(BaseModel):
    summary_text_hindi: str = Field(description="Summary of the phone call in Hindi")
    summary_text_english: str = Field(description="Summary of the phone call in English")
    target_crop: Optional[str] = Field(description="The specific crop being discussed by the farmer on the call (e.g. Wheat, Soyabean, Cotton). If multiple, state the primary one. If not mentioned, return null.", default=None)
    key_recommendations: List[str] = Field(description="List of key recommendations given to the farmer", default_factory=list)
    products_mentioned: List[str] = Field(description="List of products or chemicals suggested to the farmer", default_factory=list)
    farmer_satisfaction: int = Field(description="Rate farmer satisfaction from 1 to 5. 5 is very satisfied, 1 is frustrated or angry.", ge=1, le=5)
    symptoms_detected: int = Field(description="Number of distinct symptoms identified", ge=0)
    advisory_confidence: float = Field(description="Confidence in the advisory given, from 0.0 to 1.0", ge=0.0, le=1.0)
    was_escalated: bool = Field(description="Whether the call felt escalated or needed human intervention", default=False)
    escalation_reason: Optional[str] = Field(description="Reason for escalation, if applicable", default=None)
    call_outcome: CallOutcome = Field(description="Final outcome of the call")

async def generate_post_call_summary(session_id: str, provider_call_id: str, organisation_id: int, company_id: Optional[int] = None):
    """
    Fetches the conversation from the LangGraph checkpointer,
    analyzes it using the LLM, and inserts CallSummary and CallMetrics.
    """
    try:
        # Fetch conversation state
        executor = await get_agent_executor(organisation_id=organisation_id, company_id=company_id)
        
        # In langchain graph, the thread ID is what we pass to checkpointer
        state = await executor.aget_state({"configurable": {"thread_id": provider_call_id}})
        
        if not state or 'messages' not in state.values:
            # Maybe the thread ID was just session_id?
            state = await executor.aget_state({"configurable": {"thread_id": session_id}})
            if not state or 'messages' not in state.values:
                logger.warning(f"No conversation history found for session {session_id} or {provider_call_id}")
                return
                
        messages = state.values['messages']
        
        if len(messages) <= 1:
            logger.info("Conversation too short for meaningful summary.")
            return

        transcript = ""
        for m in messages:
            if getattr(m, 'type', '') == 'human':
                transcript += f"Farmer: {m.content}\n"
            elif getattr(m, 'type', '') == 'ai':
                transcript += f"KisanVani: {m.content}\n"

        if not transcript.strip():
            logger.info("Transcript is empty, skipping summary.")
            return

        # Prepare LLM extraction
        llm = await get_llm()
        structured_llm = llm.with_structured_output(CallSummaryMetricsPayload)
        
        prompt = f"""
        Analyze the following transcript of a conversation between a farmer and KisanVani (AI agricultural advisor).
        Extract a brief bilingual summary, key recommendations, any specific products/medicines mentioned, and overall metrics.
        The conversation is typically in Hindi/Hinglish.
        
        Transcript:
        {transcript}
        """

        extraction: CallSummaryMetricsPayload = await structured_llm.ainvoke(prompt)
        
        # Save to database
        async with AsyncSessionLocal() as db:
            call_obj = (await db.execute(select(CallSession).where(
                (CallSession.session_id == session_id) | (CallSession.provider_call_id == provider_call_id)
            ))).scalar_one_or_none()
            
            if not call_obj:
                logger.error(f"Cannot associate summary with missing CallSession: {session_id}")
                return
                
            # Create CallSummary
            summary = CallSummary(
                call_session_id=call_obj.id,
                target_crop=extraction.target_crop,
                summary_text_hindi=extraction.summary_text_hindi,
                summary_text_english=extraction.summary_text_english,
                key_recommendations=extraction.key_recommendations,
                products_mentioned=extraction.products_mentioned,
            )
            db.add(summary)
            
            # Create CallMetrics
            metrics = CallMetrics(
                call_session_id=call_obj.id,
                organisation_id=organisation_id,
                total_duration_seconds=call_obj.duration_seconds,
                symptoms_detected=extraction.symptoms_detected,
                advisory_confidence=extraction.advisory_confidence,
                was_escalated=extraction.was_escalated,
                escalation_reason=extraction.escalation_reason,
                farmer_satisfaction=extraction.farmer_satisfaction,
                call_outcome=extraction.call_outcome
            )
            db.add(metrics)
            
            await db.commit()
            logger.info(f"Successfully generated post-call summary and metrics for {session_id}")

    except Exception as e:
        logger.error(f"Error generating post-call summary for {session_id}: {e}", exc_info=True)
