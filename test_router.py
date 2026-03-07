import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from dotenv import load_dotenv

load_dotenv()

async def test():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    messages = [
        ToolMessage(content="test output", tool_call_id="call_abc123"),
        AIMessage(content="I see.", tool_calls=[]),
        HumanMessage(content="Hello")
    ]
    try:
        res = await llm.ainvoke(messages)
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
