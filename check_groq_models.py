import os
from groq import Groq
try:
    from config import Config
except ImportError:
    pass

api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    # Try to load from .env directly if Config fails
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv('GROQ_API_KEY')

if not api_key:
    print("Error: GROQ_API_KEY not found.")
else:
    client = Groq(api_key=api_key)
    try:
        print("Available Groq Models:")
        models = client.models.list()
        for m in models.data:
            print(f"- {m.id}")
    except Exception as e:
        print(f"Error listing models: {e}")
