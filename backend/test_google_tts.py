import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_google_tts():
    print("=" * 50)
    print("🧪 Testing Google TTS")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('GOOGLE_TTS_API_KEY')
    if api_key:
        print(f"✅ API Key found: {api_key[:20]}...")
    else:
        print("❌ API Key not found!")
        return
    
    try:
        # Import provider
        from voice.providers.google_tts import GoogleTTSProvider
        print("✅ GoogleTTSProvider imported!")
        
        # Initialize
        tts = GoogleTTSProvider(api_key=api_key)
        print("✅ Provider initialized!")
        
        # Test synthesis
        test_text = "नमस्ते, मैं किसान वाणी हूँ।"
        print(f"\n🎤 Synthesizing: '{test_text}'")
        
        audio = await tts.synthesize(test_text, language='hi')
        
        if audio and len(audio) > 0:
            # Save audio
            with open('test_output.wav', 'wb') as f:
                f.write(audio)
            print(f"✅ Success! Audio saved: test_output.wav")
            print(f"📊 Size: {len(audio):,} bytes ({len(audio)/1024:.1f} KB)")
        else:
            print("❌ No audio generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_google_tts())
