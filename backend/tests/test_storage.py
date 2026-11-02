from unittest.mock import MagicMock, patch

import pytest
from api.storage import LocalStorage, S3Storage


def test_local_save_open_delete(tmp_path):
    storage = LocalStorage(str(tmp_path))
    key = "resumes/abc/def.pdf"
    storage.save(key, b"hello", "application/pdf")
    with storage.open(key) as fh:
        assert fh.read() == b"hello"
    storage.delete(key)
    assert not (tmp_path / key).exists()


def test_local_rejects_path_escape(tmp_path):
    storage = LocalStorage(str(tmp_path))
    with pytest.raises(ValueError):
        storage.save("../escape.pdf", b"x", "application/pdf")


def test_s3_save_uses_sse_without_network():
    with patch("boto3.client") as mock_client:
        client = MagicMock()
        mock_client.return_value = client
        storage = S3Storage("my-bucket", "us-west-2")
        storage.save("resumes/a/b.pdf", b"data", "application/pdf")
    client.put_object.assert_called_once()
    kwargs = client.put_object.call_args.kwargs
    assert kwargs["ServerSideEncryption"] == "AES256"
    assert kwargs["Bucket"] == "my-bucket"
