# OpenAI API Anbindung
import os
from dotenv import load_dotenv
from openai import OpenAI

# Env laden
load_dotenv(override=True)

# API-Key Check
api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not (api_key.startswith("sk-") and len(api_key) > 40):
    raise RuntimeError("OPENAI_API_KEY fehlt oder ist ungültig. Bitte in .env prüfen.")

# Client Setup
_client = OpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"

# Chat-Funktion für KI
def chat(messages, temperature=0.2):
    resp = _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature
    )
    return resp.choices[0].message
