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
            'en': 'Respond in English and ONLY in ENGLISH!.',
            'de': 'Respond in German and ONLY in GERMAN!',
            'es': 'Respond in Spanish and ONLY in SPANISH!',
            'fr': 'Respond in French and ONLY in FRENCH!',
            'it': 'Respond in Italian and ONLY in ITALIAN!',
            'pt': 'Respond in Portuguese and ONLY in PORTUGUESE!',
        }

        language_instruction = language_instructions.get(language, language_instructions['en'])

        prompt = (
                "You are a financial advisor AI. You provide budgeting suggestions based on transactional data of a user.\n\n"
                "**Your task**\n"
                "Provide exactly 3 specific, actionable budgeting suggestions and a brief analysis based on the following context:\n\n"
                + str(context) +
                "\n\n"
                f"{language_instruction}\n\n"
                "**Response Format**\n"
                "__SUGGESTIONS__:\n"
                "1. [First suggestion]\n"
                "2. [Second suggestion]\n"
                "3. [Third suggestion]\n\n"
                "__ANALYSIS__:\n"
                "[Your brief analysis of spending patterns]\n"
        )
        log.info("BEGIN prompt")
        log.info(prompt)
        log.info("END prompt")
        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60,  # Increased from 10 to 60 seconds to allow Ollama time to generate
            )
            if resp.ok:
                data = resp.json()
                text = data.get("response", "")
                suggestions, analysis = self._parse_response(text)
                return {"suggestions": suggestions, "analysis": analysis}
        except Exception:
            log.exception("Failed to generate insights")
        return {"suggestions": ["Reduce discretionary spending."], "analysis": "Ollama unavailable; fallback output."}

    def _parse_response(self, text: str) -> tuple[list[str], str]:
        """Parse Ollama response into suggestions and analysis."""
        suggestions = []
        analysis = ""

        # Strip everything before SUGGESTIONS
        if "__SUGGESTIONS__:" in text:
            text = text[text.index("__SUGGESTIONS__:"):]

        # Split by ANALYSIS section
        sections = text.split("__ANALYSIS__:")
        suggestions_section = sections[0].replace("__SUGGESTIONS__:", "").strip()
        analysis = sections[1].strip() if len(sections) > 1 else ""

        # Clean analysis (remove asterisks, extra whitespace)
        analysis = analysis.strip("* \n").strip()

        # Extract suggestions (numbered format: 1. 2. 3.)
        lines = suggestions_section.split("\n")
        for line in lines:
            line = line.strip()
            # Match patterns like "1. suggestion" or "- suggestion"
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove number/dash/asterisks and clean up
                suggestion = line.lstrip("0123456789.-*").strip()
                if suggestion and len(suggestions) < 3:
                    suggestions.append(suggestion)

        return suggestions, analysis


provider = OllamaProvider()
