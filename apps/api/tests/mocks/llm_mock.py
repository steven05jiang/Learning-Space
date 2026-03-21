import json


class MockLLMClient:
    """Returns predictable LLM responses for integration tests."""

    async def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "title": "Mock Resource Title",
                "summary": "This is a mock summary for integration testing.",
                "tags": ["AI", "Testing", "Mock"],
            }
        )
