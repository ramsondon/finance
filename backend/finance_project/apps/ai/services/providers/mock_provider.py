class MockProvider:
    name = "mock"

    def generate_insights(self, user_id: int, context: dict) -> dict:
        return {
            "suggestions": [
                "Consider reviewing recurring subscriptions.",
                "Set a monthly savings goal.",
            ],
            "analysis": "This is a mock analysis based on your recent transactions.",
        }


provider = MockProvider()

