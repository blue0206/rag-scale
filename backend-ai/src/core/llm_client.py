from openai import OpenAI
from .config import env_config

llm_client = OpenAI(
    api_key=env_config["GROQ_API_KEY"],
    base_url=env_config["GROQ_BASE_URL"],
)
