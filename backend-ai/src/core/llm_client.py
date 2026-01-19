from openai import AsyncOpenAI
from .config import env_config

class LLMService:
    def __init__(self, api_key: str, base_url: str):
        self.client: AsyncOpenAI | None = None
        self.connection_details = (api_key, base_url)

    def connect(self) -> None:
        """
        Connects the Async OpenAI Client.
        """
        if not self.client:
            self.client = AsyncOpenAI(
                api_key=self.connection_details[0],
                base_url=self.connection_details[1]
            )
            print("Async OpenAI Client connected.")

    async def disconnect(self) -> None:
        """
        Disconnects the Async OpenAI Client.
        """
        if self.client is not None:
            await self.client.close()
            self.client = None
            print("Async OpenAI Client disconnected.")

    def get_client(self) -> AsyncOpenAI:
        if not self.client:
            self.connect()

        assert self.client is AsyncOpenAI
        return self.client

llm_service = LLMService(api_key=env_config.GROQ_API_KEY, base_url=env_config.GROQ_BASE_URL)
llm_client = llm_service.get_client()
