import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma:2b')
    UPLOAD_FOLDER = 'static/downloads'
    OUTPUT_FOLDER = 'static/output'
    FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe" # Explicit path to ffmpeg
    
    # Ensure directories exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
