from contextlib import asynccontextmanager
from typing import AsyncGenerator
from openai import AsyncOpenAI
from .config import env_config

class LLMService:
    def __init__(self, api_key: str, base_url: str):
        self.client: AsyncOpenAI | None = None
        self.connection_details = (api_key, base_url)

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AsyncOpenAI, None]:
        """
        Returns the async OpenAI client.
        """

        openai_client = AsyncOpenAI(
                api_key=self.connection_details[0],
                base_url=self.connection_details[1]
            )
        
        try:
            yield openai_client
        finally:
            await openai_client.close()
            print("OpenAI client context closed.")

llm_service = LLMService(api_key=env_config.GROQ_API_KEY, base_url=env_config.GROQ_BASE_URL)
