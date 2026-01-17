import motor.motor_asyncio
from ..core.config import env_config

client = motor.motor_asyncio.AsyncIOMotorClient(
    f"mongodb://{env_config.MONGO_DB_ROOT_USERNAME}:{env_config.MONGO_DB_ROOT_PASSWORD}@localhost:27017/ragscale_db?authSource=admin"
)
mongo_client = client.ragscale_db

users_collection = mongo_client.get_collection("users")
sessions_collection = mongo_client.get_collection("sessions")
