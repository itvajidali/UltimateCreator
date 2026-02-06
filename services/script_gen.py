import os
import json
import time
from groq import Groq
try:
    from config import Config
except ImportError:
    from ..config import Config

from services.search_engine import search_web

def generate_script(prompt, duration, voice_id="en-US", api_key=None):
    """
    Generates a script using Groq API (Llama-3-70B).
    """
    # Use Groq API Key from Config
    api_key = Config.GROQ_API_KEY
    if not api_key:
        print("Error: No Groq API Key provided.")
        return [{"text": "Error: Groq API Key missing.", "image_query": "error"}]

    client = Groq(api_key=api_key)
    
    # Calculate limits
    if duration == 'short':
        num_segments = 5
    elif duration == 'medium':
        num_segments = 10
    else: # long
        num_segments = 20

    language_instruction = "ENGLISH"
    if "hi-IN" in voice_id:
        language_instruction = "HINDI (Devanagari Script). IMPORTANT: Write the 'text' in clear Hindi, but keep 'image_query' in English."

    # Live Search Logic
    context_part = ""
    # Simple keyword check for "news" intent
    news_keywords = ["news", "latest", "update", "today", "current", "trending", "headline"]
    if any(k in prompt.lower() for k in news_keywords):
        print(f"News intent detected for '{prompt}'. Searching web...")
        search_results = search_web(prompt)
        if search_results:
            context_part = f"\n\n[REAL-TIME SEARCH CONTEXT]\n{search_results}\n\nINSTRUCTION: Use the above Real-Time Context to write the script. Verify facts from it."

    system_instruction = f"""
    Role: Professional Video Script Writer.
    Input: "{prompt}"
    {context_part}
    Goal: Create a detailed, engaging video script.
    
    Instructions:
    1. If the Input is a TOPIC (e.g. "Facts about Cars"): Write a script about it.
    2. If the Input is a QUESTION (e.g. "How does rain happen?"): Answer it in a video script format.
    3. If the Input is a LONG SCRIPT (e.g. "Hello everyone, today we..."): KEEP the text exactly as is (or translate if needed), just split it into segments and add visual cues.
    
    Constraints:
    1. Language for Narration ('text'): {language_instruction}
    2. Duration: Approximately {num_segments} segments (Ignore if Custom Script).
    3. Output Format: STRICT JSON Array.
    
    Each segment must have:
    - "text": The narration script (in {language_instruction}).
    - "image_query": A specific, visual English keyword for stock footage search.
    - "image_query": A specific, visual English keyword for stock footage search.

    Example Output:
    [
      {{ "text": "India is a land of vibrant culture.", "image_query": "india culture festival" }},
      {{ "text": "Taj Mahal is a symbol of love.", "image_query": "taj mahal drone shot" }}
    ]
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_instruction
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=8000,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"}
        )

        text = completion.choices[0].message.content.strip()
        
        # Log for debugging
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"--- GROQ PROMPT ---\n{system_instruction}\n--- OUTPUT ---\n{text}\n----------------\n")
        
        # Parse JSON
        data = json.loads(text)
        
        # Groq sometimes wraps array in an object like {"segments": [...]}, check for list
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
             # Try to find the list inside
             for key in data:
                 if isinstance(data[key], list):
                     return data[key]
        
        return [{"text": "Error: AI output format invalid.", "image_query": "error"}]

    except Exception as e:
        err_msg = f"Groq Error: {e}"
        print(err_msg)
        with open('debug_log.txt', 'a') as f:
            f.write(f"{err_msg}\n")
def translate_script(script_data, target_language, api_key=None):
    """
    Translates the 'text' fields of the script to the target language using Groq.
    """
    api_key = api_key or Config.GROQ_API_KEY
    client = Groq(api_key=api_key)
    
    system_instruction = f"""
    Role: Professional Translator.
    Goal: Translate the 'text' field of the provided JSON to {target_language}.
    Constraints:
    1. KEEP 'image_query' EXACTLY THE SAME (Do not translate visual cues).
    2. Translate 'text' so it sounds natural in spoken {target_language}.
    3. Output the exact same JSON structure.
    """
    
    user_content = json.dumps(script_data)
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3, # Low temp for accurate translation
            response_format={"type": "json_object"}
        )
        
        text = completion.choices[0].message.content.strip()
        data = json.loads(text)
        
        # Robust parsing
        if isinstance(data, list): return data
        if isinstance(data, dict):
             for key in data:
                 if isinstance(data[key], list): return data[key]
                 
        return script_data # Fallback to original

    except Exception as e:
        print(f"Translation failed: {e}")
        return script_data # Fallback
