class MockProvider:
    name = "mock"

    def generate_insights(self, user_id: int, context: dict, language: str = 'en') -> dict:
        # Localized suggestions based on language
        suggestions_map = {
            'en': [
                "Consider reviewing recurring subscriptions.",
                "Set a monthly savings goal.",
            ],
            'de': [
                "Überprüfen Sie regelmäßig Ihre wiederkehrenden Abonnements.",
                "Setzen Sie sich ein monatliches Sparziel.",
            ],
            'es': [
                "Considere revisar sus suscripciones recurrentes.",
                "Establezca una meta de ahorro mensual.",
            ],
            'fr': [
                "Examinez vos abonnements récurrents.",
                "Fixez-vous un objectif d'épargne mensuel.",
            ],
        }

        analysis_map = {
            'en': "This is a mock analysis based on your recent transactions.",
            'de': "Dies ist eine simulierte Analyse basierend auf Ihren letzten Transaktionen.",
            'es': "Este es un análisis simulado basado en sus transacciones recientes.",
            'fr': "Ceci est une analyse simulée basée sur vos transactions récentes.",
        }

        suggestions = suggestions_map.get(language, suggestions_map['en'])
        analysis = analysis_map.get(language, analysis_map['en'])

        return {
            "suggestions": suggestions,
            "analysis": analysis,
        }


provider = MockProvider()

