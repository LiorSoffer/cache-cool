import json
from pymongo import MongoClient
import redis
from app.core.config import settings
from collections import OrderedDict
import os
from datetime import datetime


class CacheService:
    def __init__(self):
        self.use_json_cache = settings.use_json_cache
        self.use_mongo_cache = settings.use_mongo_cache
        self.max_cache_size = settings.cache_max_size
        if self.use_mongo_cache:
            self.mongo_client = MongoClient(settings.mongodb.uri)
            self.mongo_db = self.mongo_client[settings.mongodb.db_name]
            self.mongo_collection = self.mongo_db[settings.mongodb.collection_name]
        if settings.redis.enabled:
            self.redis_client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                db=settings.redis.db,
            )

    def _load_json_cache(self) -> OrderedDict:
        try:
            if os.path.exists(settings.json_cache_file):
                with open(settings.json_cache_file, "r") as f:
                    data = json.load(f)
                    return OrderedDict(data)
        except json.JSONDecodeError:
            pass
        return OrderedDict()

    def _save_json_cache(self, cache: OrderedDict):
        with open(settings.json_cache_file, "w") as f:
            json.dump(cache, f)

    async def get(self, key: str):
        if settings.redis.enabled:
            redis_result = self.redis_client.get(key)
            if redis_result:
                return json.loads(redis_result)

        if self.use_mongo_cache:
            mongo_result = self.mongo_collection.find_one({"_id": key})
            if mongo_result:
                return mongo_result["response"]

        if self.use_json_cache:
            cache = self._load_json_cache()
            if key in cache:
                return cache[key]

        return None

    async def set(self, key: str, value: str, expire: int = 3600):
        if settings.redis.enabled:
            self.redis_client.setex(key, expire, json.dumps(value))

        if self.use_mongo_cache:
            count = self.mongo_collection.count_documents({})
            if count >= self.max_cache_size:
                oldest = self.mongo_collection.find_one(
                    sort=[("insertedAt", 1)]  # Ascending → oldest inserted first (FIFO)
                )
                if oldest:
                    self.mongo_collection.delete_one({"_id": oldest["_id"]})
                    print(f"Evicted FIFO key: {oldest['_id']}")

            self.mongo_collection.update_one(
                {"_id": key},
                {
                    "$set": {"response": value},
                    "$setOnInsert": {"insertedAt": datetime.utcnow()},
                },
                upsert=True,
            )

        if self.use_json_cache:
            cache = self._load_json_cache()

            if key not in cache and len(cache) >= self.max_cache_size:
                evicted_key, _ = cache.popitem(last=False)  # Remove (first) item
                print(f"Evicted FIFO key: {evicted_key}")

            cache[key] = value
            self._save_json_cache(cache)

    async def delete(self, key: str):
        if settings.redis.enabled:
            self.redis_client.delete(key)

        if self.use_mongo_cache:
            self.mongo_collection.delete_one({"_id": key})

        if self.use_json_cache:
            cache = self._load_json_cache()
            if key in cache:
                del cache[key]
                self._save_json_cache(cache)
