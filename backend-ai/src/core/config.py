from dotenv import load_dotenv
import os

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("Missing environment variables.")

env_config = {
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY")
}
