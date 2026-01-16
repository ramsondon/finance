import logging

import requests
import os

log = logging.getLogger(__name__)


class OllamaProvider:
    name = "ollama"

    def __init__(self, host: str | None = None, model: str | None = None):
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")

    def generate_insights(self, user_id: int, context: dict, language: str = 'en') -> dict:
        # Language instruction mapping
        language_instructions = {
            'en': 'Respond in English.',
            # 'de': 'Antworte auf Deutsch.',
            # 'es': 'Responde en español.',
            # 'fr': 'Répondez en français.',
            # 'it': 'Rispondi in italiano.',
            # 'pt': 'Responda em português.',
            'de': 'Respond in German.',
            'es': 'Respond in Spanish.',
            'fr': 'Respond in French.',
            'it': 'Respond in Italian.',
            'pt': 'Respond in Portuguese.',
        }

        language_instruction = language_instructions.get(language, language_instructions['en'])

        prompt = (
            "You are a financial advisor AI. You provide budgeting suggestions based on transactional data of a user.\n\n"
            "**Your task**\n"
            "Provide exactly 3 specific, actionable budgeting suggestions and a brief analysis based on the following context:\n\n"
            + str(context) +
            "\n\n"
            f"{language_instruction}\n\n"
            "** Response Format**\n"
            "SUGGESTIONS:\n"
            "1. [First suggestion]\n"
            "2. [Second suggestion]\n"
            "3. [Third suggestion]\n\n"
            "ANALYSIS:\n"
            "[Your brief analysis of spending patterns]\n"
        )
        log.debug(prompt)
        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60,  # Increased from 10 to 60 seconds to allow Ollama time to generate
            )
            if resp.ok:
                data = resp.json()
                text = data.get("response", "")
                suggestions = [s.strip("- ") for s in text.split("\n") if s.strip()][:3]
                return {"suggestions": suggestions, "analysis": text}
        except Exception:
            log.exception("Failed to generate insights")
        return {"suggestions": ["Reduce discretionary spending."], "analysis": "Ollama unavailable; fallback output."}


provider = OllamaProvider()
