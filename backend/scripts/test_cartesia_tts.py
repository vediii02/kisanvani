import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from services.voice.tts_node import CartesiaTTS
from services.voice.events import TTSChunkEvent

async def test_cartesia():
    load_dotenv()
    api_key = os.getenv("CARTESIA_API_KEY")
    if not api_key:
        print("Error: CARTESIA_API_KEY not found in .env")
        return

    print("Initializing CartesiaTTS...")
    # Using a known good Indian female voice ID
    tts = CartesiaTTS(api_key=api_key, voice_id="3b554273-4299-48b9-9aaf-eefd438e3941", language="hi")
    
    test_text = "नमस्ते, मैं आपकी कैसे मदद कर सकता हूँ? क्या आपके पास खेतों के बारे में कोई सवाल है?"
    print(f"Sending text: {test_text}")
    
    await tts.send_text(test_text, turn_id=1)
    await tts.flush_tts()
    
    print("Waiting for audio chunks...")
    chunks = []
    try:
        # Wait up to 10 seconds for audio
        while True:
            try:
                event = await asyncio.wait_for(tts.output_queue.get(), timeout=3.0)
                if isinstance(event, TTSChunkEvent):
                    print(f"Received chunk: {len(event.audio)} bytes")
                    chunks.append(event.audio)
                else:
                    print(f"Received unexpected event: {type(event)}")
            except asyncio.TimeoutError:
                print("No more chunks received.")
                break
    finally:
        await tts.close()

    if chunks:
        output_file = "cartesia_test_output.pcm"
        with open(output_file, "wb") as f:
            for chunk in chunks:
                f.write(chunk)
        print(f"Saved {len(chunks)} chunks to {output_file} (Total: {sum(len(c) for c in chunks)} bytes)")
        print(f"To play this raw PCM (8kHz, s16le): ffplay -f s16le -ar 8000 -ac 1 {output_file}")
    else:
        print("No audio chunks generated.")

if __name__ == "__main__":
    asyncio.run(test_cartesia())
