import httpx
import os

async def ask_gemini(question: str):
    api_key = os.getenv("GEMINI_API_KEY")
    endpoint = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "contents": [{"parts": [{"text": question}]}]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, headers=headers, json=payload)
    return response.json()
