from functools import lru_cache

from django.conf import settings
from pymongo import MongoClient


@lru_cache(maxsize=1)
def get_database():
    # tz_aware=True so PyMongo returns timezone-aware UTC datetimes instead of naive ones.
    client = MongoClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=1500,
        tz_aware=True,
    )
    client.admin.command("ping")
    return client[settings.MONGODB_DATABASE]
