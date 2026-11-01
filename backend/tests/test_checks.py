from api.checks import check_dev_auth_not_in_prod, check_secret_key_in_prod
from django.test import override_settings


@override_settings(CAREERS_DEV_AUTH=True, DEBUG=False)
def test_e001_fires_dev_auth_in_prod():
    errors = check_dev_auth_not_in_prod(None)
    assert [e.id for e in errors] == ["careers.E001"]


@override_settings(CAREERS_DEV_AUTH=True, DEBUG=True)
def test_e001_silent_in_debug():
    assert check_dev_auth_not_in_prod(None) == []


@override_settings(CAREERS_DEV_AUTH=False, DEBUG=False)
def test_e001_silent_without_dev_auth():
    assert check_dev_auth_not_in_prod(None) == []


@override_settings(DEBUG=False, SECRET_KEY="local-development-only")
def test_e002_fires_default_secret_in_prod():
    errors = check_secret_key_in_prod(None)
    assert [e.id for e in errors] == ["careers.E002"]


@override_settings(DEBUG=False, SECRET_KEY="a-real-strong-secret")
def test_e002_silent_with_real_secret():
    assert check_secret_key_in_prod(None) == []


@override_settings(DEBUG=True, SECRET_KEY="local-development-only")
def test_e002_silent_in_debug():
    assert check_secret_key_in_prod(None) == []
