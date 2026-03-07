import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": None, "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "test", "arguments": "{}"}}]},
                {"role": "user", "content": "Wait nevermind"},
                {"role": "tool", "tool_call_id": "call_123", "name": "test", "content": "Interrupted"},
            ],
            tools=[{"type": "function", "function": {"name": "test", "description": "test"}}]
        )
        print("Success:", response.choices[0].message.content)
    except Exception as e:
        print("Error:", repr(e))

asyncio.run(main())
