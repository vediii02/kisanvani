#!/usr/bin/env python3
"""
Generate Static Audio Files using gTTS (No API Key Required)
Creates greeting_hi.mp3 and error_hi.mp3
"""

from gtts import gTTS
import os
from pathlib import Path

def generate_audio_files():
    """Generate static audio files using gTTS"""
    
    print("🎙️ Generating audio files using gTTS (No API key needed)...")
    
    # Audio content in Hindi
    audio_files = {
        "greeting_hi.mp3": "नमस्ते। किसान वाणी में आपका स्वागत है। कृपया अपना प्रश्न बताएं।",
        "error_hi.mp3": "क्षमा करें, कुछ गलत हो गया। कृपया फिर से कोशिश करें।",
        "thankyou_hi.mp3": "धन्यवाद। किसान वाणी में फिर से कॉल करें।"
    }
    
    # Output directory
    output_dir = Path("static/audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for filename, text in audio_files.items():
        try:
            print(f"\n📝 Generating {filename}...")
            print(f"   Text: {text}")
            
            # Generate audio using gTTS
            tts = gTTS(text=text, lang='hi', slow=False)
            
            # Save to file
            filepath = output_dir / filename
            tts.save(str(filepath))
            
            # Get file size
            file_size = filepath.stat().st_size / 1024  # KB
            print(f"✅ Generated {filename} ({file_size:.1f} KB)")
            
        except Exception as e:
            print(f"❌ Error generating {filename}: {e}")
    
    print("\n" + "="*60)
    print("✅ Audio file generation complete!")
    print(f"📂 Files saved in: {output_dir}/")
    print("\n🔗 URLs for Exotel:")
    print("   Greeting:  https://kisan.rechargestudio.com/static/audio/greeting_hi.mp3")
    print("   Error:     https://kisan.rechargestudio.com/static/audio/error_hi.mp3")
    print("   Thank You: https://kisan.rechargestudio.com/static/audio/thankyou_hi.mp3")
    print("="*60)
    
    # List generated files
    print("\n📋 Generated Files:")
    for file in output_dir.glob("*.mp3"):
        size = file.stat().st_size / 1024
        print(f"   • {file.name} - {size:.1f} KB")


if __name__ == "__main__":
    try:
        generate_audio_files()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        exit(1)
