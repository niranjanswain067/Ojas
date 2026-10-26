"""Unit tests for configuration system (Phase 2)."""

import pytest
from backend.app.config import OjasSettings, get_settings


def test_settings_load_defaults():
    settings = get_settings()
    assert settings.port == 8000
    assert settings.host == "127.0.0.1"
    assert settings.temperature == 0.2
    assert settings.iteration_limit == 5


def test_settings_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_port_validation():
    with pytest.raises(ValueError):
        OjasSettings(port=80)

    with pytest.raises(ValueError):
        OjasSettings(port=99999)

    valid = OjasSettings(port=8080)
    assert valid.port == 8080
