import os
import pytest
from unittest.mock import patch

from core.config import Settings, get_settings


def test_default_settings_load():
    s = Settings()
    assert s.environment == "development"
    assert s.debug is False
    assert "learningspace" in s.database_url
    assert s.neo4j_user == "neo4j"
    assert s.openai_model == "gpt-4o-mini"


def test_env_override():
    with patch.dict(os.environ, {"DEBUG": "true", "OPENAI_MODEL": "gpt-4o"}):
        # Force a fresh Settings parse (bypass cache)
        s = Settings()
        assert s.debug is True
        assert s.openai_model == "gpt-4o"


def test_get_settings_returns_same_instance():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2