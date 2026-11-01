"""Create every collection's indexes idempotently.

MongoDB treats an identical existing index as a no-op, so running this twice succeeds.
"""

from django.core.management.base import BaseCommand

from api.indexes import INDEXES
from api.mongo import get_database


class Command(BaseCommand):
    help = "Create MongoDB indexes for every collection (idempotent)."

    def handle(self, *args, **options):
        db = get_database()
        for collection_name, models in INDEXES.items():
            if not models:
                continue
            names = db[collection_name].create_indexes(models)
            self.stdout.write(f"{collection_name}: ensured {len(names)} index(es): {names}")
        self.stdout.write(self.style.SUCCESS("Indexes ensured."))
