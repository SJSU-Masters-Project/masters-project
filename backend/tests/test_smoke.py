from django.conf import settings


def test_test_database_is_isolated(db):
    assert settings.MONGODB_DATABASE.startswith("careers_test_")


def test_collections_empty_at_test_start(db):
    assert db.users.count_documents({}) == 0
    assert db.events.count_documents({}) == 0
