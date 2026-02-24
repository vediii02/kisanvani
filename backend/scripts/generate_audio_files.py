#!/usr/bin/env python3
"""
Generate Static Audio Files for Exotel Integration
Creates greeting_hi.mp3 and error_hi.mp3 using Google TTS
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice.providers.google_tts import GoogleTTSProvider


async def generate_audio_files():
    """Generate static audio files for Exotel"""
    
    print("🎙️ Generating static audio files for Exotel...")
    
    # Set API key if available
    api_key = os.getenv("GOOGLE_TTS_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No Google API key found in environment")
        print("   Set GOOGLE_TTS_API_KEY or GOOGLE_API_KEY")
        return
    
    # Initialize TTS provider
    tts = GoogleTTSProvider(api_key=api_key)
    
    audio_files = {
        "greeting_hi.mp3": "नमस्ते। किसान वाणी में आपका स्वागत है। कृपया अपना प्रश्न बताएं।",
        "error_hi.mp3": "क्षमा करें, कुछ गलत हो गया। कृपया फिर से कोशिश करें।"
    }
    
    output_dir = "static/audio"
    os.makedirs(output_dir, exist_ok=True)
    
    for filename, text in audio_files.items():
        try:
            print(f"📝 Generating {filename}...")
            print(f"   Text: {text}")
            
            # Generate audio
            audio_bytes = await tts.synthesize(text=text, language="hi")
            
            if not audio_bytes:
                print(f"❌ Failed to generate {filename}")
                continue
            
            # Save to file
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
            
            file_size = len(audio_bytes) / 1024  # KB
            print(f"✅ Generated {filename} ({file_size:.1f} KB)")
            
        except Exception as e:
            print(f"❌ Error generating {filename}: {e}")
    
    print("\n✅ Audio file generation complete!")
    print(f"📂 Files saved in: {output_dir}/")
    print("\n🔗 URLs for Exotel:")
    print("   Greeting: https://kisan.rechargestudio.com/static/audio/greeting_hi.mp3")
    print("   Error:    https://kisan.rechargestudio.com/static/audio/error_hi.mp3")


if __name__ == "__main__":
    asyncio.run(generate_audio_files())
