import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def call_llm(system_prompt: str, user_prompt: str) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = os.getenv("MODEL_NAME", "meta-llama/llama-3.1-8b-instruct")
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"} 
            }
        )
        if response.status_code == 200:
            return json.loads(response.json()['choices'][0]['message']['content'])
        return {}
    except Exception:
        return {}