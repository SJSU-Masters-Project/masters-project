import os
from uuid import uuid4

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_DEBUG", "true")
os.environ.setdefault("CAREERS_DEV_AUTH", "true")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

django.setup()


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Use a fresh database for the whole session and drop it at the end."""
    from api.mongo import get_database
    from django.conf import settings
    from django.core.management import call_command

    settings.CAREERS_DEV_AUTH = True
    settings.MONGODB_DATABASE = f"careers_test_{uuid4().hex[:8]}"
    get_database.cache_clear()

    db = get_database()
    call_command("ensure_indexes")
    yield db

    db.client.drop_database(db.name)
    get_database.cache_clear()


@pytest.fixture(autouse=True)
def _clean_collections(_test_database):
    """Empty every collection after each test, keeping indexes."""
    yield
    db = _test_database
    for name in db.list_collection_names():
        db[name].delete_many({})


@pytest.fixture
def db(_test_database):
    return _test_database


@pytest.fixture
def api():
    from rest_framework.test import APIClient

    return APIClient()


def as_user(api_client, email, role):
    """Attach a dev auth header for the given email/role to the client."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer dev:{email}:{role}")
    return api_client
