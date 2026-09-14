from functools import lru_cache
from pymongo import MongoClient
from django.conf import settings

@lru_cache(maxsize=1)
def get_database():
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=1500)
    client.admin.command("ping")
    return client[settings.MONGODB_DATABASE]

