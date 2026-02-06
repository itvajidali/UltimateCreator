import asyncio
import edge_tts
import os
from config import Config

async def _generate_audio_async(text, voice_id, output_path):
    # Tweak settings for better quality
    # Slower rate often sounds less robotic for Hindi
    rate = "-5%" if "hi-IN" in voice_id else "+0%"
    pitch = "+0Hz"
    
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, pitch=pitch)
    await communicate.save(output_path)

def generate_audio(text, voice_id):
    """
    Generates audio for the given text and returns the path to the file.
    """
    # Create unique filename for this segment
    import hashlib
    hash_object = hashlib.md5(text.encode())
    filename = hash_object.hexdigest() + ".mp3"
    output_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    
    if os.path.exists(output_path):
        return output_path

    # Run async function in sync wrapper
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_generate_audio_async(text, voice_id, output_path))
    loop.close()
    
    return output_path
