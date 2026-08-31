import pytest

from app.config import ProviderConfig
from app.proxy import ProviderError, api_key_for


def test_missing_api_key_raises():
    cfg = ProviderConfig(name="x", base_url="https://x", api_key_env="DEFINITELY_NOT_SET_12345")
    with pytest.raises(ProviderError):
        api_key_for(cfg)


def test_provider_error_message(monkeypatch):
    cfg = ProviderConfig(name="x", base_url="https://x", api_key_env="MY_KEY_XYZ")
    monkeypatch.setenv("MY_KEY_XYZ", "sk-test")
    assert api_key_for(cfg) == "sk-test"
