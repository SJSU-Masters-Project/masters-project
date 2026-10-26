"""Resume file storage backends.

Keys contain only system-generated ids, never user-supplied names.
"""

import os
from pathlib import Path
from typing import BinaryIO, Protocol

from django.conf import settings


class ResumeStorage(Protocol):
    def save(self, key: str, data: bytes, content_type: str) -> None: ...
    def open(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...


class LocalStorage:
    """Store files under ``root``; refuse any key that escapes ``root``."""

    def __init__(self, root: str):
        self.root = Path(root).resolve()

    def _resolve(self, key: str) -> Path:
        target = (self.root / key).resolve()
        if target != self.root and self.root not in target.parents:
            raise ValueError(f"Key escapes storage root: {key!r}")
        return target

    def save(self, key: str, data: bytes, content_type: str) -> None:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as fh:
            fh.write(data)

    def open(self, key: str) -> BinaryIO:
        return open(self._resolve(key), "rb")

    def delete(self, key: str) -> None:
        target = self._resolve(key)
        if target.exists():
            os.remove(target)


class S3Storage:
    """Store files in S3 with server-side AES256 encryption."""

    def __init__(self, bucket: str, region: str):
        import boto3

        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region)

    def save(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    def open(self, key: str) -> BinaryIO:
        from io import BytesIO

        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return BytesIO(obj["Body"].read())

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def get_storage() -> ResumeStorage:
    if settings.RESUME_STORAGE == "s3":
        return S3Storage(settings.RESUME_S3_BUCKET, settings.RESUME_S3_REGION)
    return LocalStorage(settings.RESUME_LOCAL_ROOT)
