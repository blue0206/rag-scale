from dotenv import load_dotenv
import os

load_dotenv()

if not os.getenv("GROQ_API_KEY") or not os.getenv("NEO4J_URI") or not os.getenv("NEO4J_USERNAME") or not os.getenv("NEO4J_PASSWORD"):
    raise ValueError("Missing one or more environment variables.")

env_config = {
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "NEO4J_URI": os.getenv("NEO4J_URI"),
    "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
    "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
    "GROQ_MODEL": "openai/gpt-oss-120b",
    "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
    "EMBEDDER_MODEL": "nomic-embed-text"
}