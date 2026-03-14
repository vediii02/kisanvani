import asyncio
from services.voice.llm import ask_agent

async def main():
    print("Sending message...")
    await ask_agent("Hello", "test_thread_1")
    print("Done 1")
    for i in range(16):
        print(f"Sending message {i}...")
        await ask_agent("My name is Ram", "test_thread_2")
    print("Done 2")

asyncio.run(main())
