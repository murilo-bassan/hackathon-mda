import os
import json
import requests
from dotenv import load_dotenv
from general_process.utilities.logger_config import setup_logger
logger = setup_logger(__name__)

load_dotenv()

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.critical("OPENROUTER_API_KEY não encontrada")
        raise ValueError("OPENROUTER_API_KEY não encontrada")

    model_name = os.getenv("MODEL_NAME", "meta-llama/llama-3.1-8b-instruct")
    
    try:

        logger.info("Enviando requisição para OpenRouter")

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "response_format": {
                    "type": "json_object"
                },
                "temperature": temperature,
            },
            timeout=60
        )
        response.raise_for_status()
        logger.info("Resposta recebida com sucesso")

    except requests.exceptions.Timeout:
        logger.error("Timeout ao chamar OpenRouter")
        return {}
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP: {e}")
        logger.error(f"Resposta da API: {response.text}")
        return {}

    except Exception as e:
        logger.exception(f"Erro inesperado: {e}")
        return {}

    try:
        content = response.json()["choices"][0]["message"]["content"]
        logger.info("Resposta parseada com sucesso")
        return json.loads(content)

    except KeyError as e:

        logger.error(f"Estrutura inesperada da resposta: {e}")
        logger.error(f"Resposta completa: {response.text}")
        return {}

    except json.JSONDecodeError as e:

        logger.error(f"Erro ao converter JSON: {e}")
        logger.error(f"Conteúdo recebido: {content}")
        return {}
