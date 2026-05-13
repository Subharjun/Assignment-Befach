from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings


class Mongo:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    settings = get_settings()
    Mongo.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=8000)
    Mongo.db = Mongo.client[settings.MONGODB_DB]
    # Indexes
    await Mongo.db.products.create_index("slug", unique=True)
    await Mongo.db.products.create_index("category")
    await Mongo.db.users.create_index("clerk_id", unique=True)
    await Mongo.db.carts.create_index("user_id", unique=True)
    await Mongo.db.conversations.create_index([("user_id", 1), ("updated_at", -1)])


async def close_mongo() -> None:
    if Mongo.client:
        Mongo.client.close()


def get_db() -> AsyncIOMotorDatabase:
    assert Mongo.db is not None, "Mongo not initialised"
    return Mongo.db
