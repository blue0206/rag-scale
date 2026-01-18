from openai import AsyncOpenAI
from .config import env_config

llm_client = AsyncOpenAI(
    api_key=env_config.GROQ_API_KEY,
    base_url=env_config.GROQ_BASE_URL,
)
