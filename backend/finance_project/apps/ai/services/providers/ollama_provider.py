import logging

import requests
import os

log = logging.getLogger(__name__)


class OllamaProvider:
    name = "ollama"

    def __init__(self, host: str | None = None, model: str | None = None):
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")

    def generate_insights(self, user_id: int, context: dict) -> dict:
        prompt = (
                "Provide 3 budgeting suggestions and a short analysis based on the following context: "
                + str(context)
        )
        log.debug(prompt)
        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=10,
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
