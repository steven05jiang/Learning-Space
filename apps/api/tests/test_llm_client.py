"""Tests for LLM client factory."""

from unittest.mock import Mock, patch

import pytest

from services.llm_client import get_direct_client, get_llm_client


class TestLLMClientFactory:
    """Test the LLM client factory functions."""

    def test_get_llm_client_anthropic(self):
        """Test LLM client factory with Anthropic provider."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.anthropic_model = "claude-haiku-4-5-20251001"

            with patch("langchain_anthropic.ChatAnthropic") as mock_chat:
                mock_client = Mock()
                mock_chat.return_value = mock_client

                result = get_llm_client()

                assert result == mock_client
                mock_chat.assert_called_once_with(
                    model="claude-haiku-4-5-20251001",
                    api_key="test-key",
                    temperature=0,
                )

    def test_get_llm_client_groq(self):
        """Test LLM client factory with Groq provider."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "groq"
            mock_settings.groq_api_key = "test-groq-key"
            mock_settings.groq_model = "llama-3.1-8b-instant"

            with patch("langchain_groq.ChatGroq") as mock_chat:
                mock_client = Mock()
                mock_chat.return_value = mock_client

                result = get_llm_client()

                assert result == mock_client
                mock_chat.assert_called_once_with(
                    model="llama-3.1-8b-instant",
                    api_key="test-groq-key",
                    temperature=0,
                )

    def test_get_llm_client_siliconflow(self):
        """Test LLM client factory with SiliconFlow provider."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "siliconflow"
            mock_settings.siliconflow_api_key = "test-sf-key"
            mock_settings.siliconflow_model = "Qwen/Qwen2.5-7B-Instruct"
            mock_settings.siliconflow_base_url = "https://api.siliconflow.com/v1"

            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_client = Mock()
                mock_chat.return_value = mock_client

                result = get_llm_client()

                assert result == mock_client
                mock_chat.assert_called_once_with(
                    model="Qwen/Qwen2.5-7B-Instruct",
                    api_key="test-sf-key",
                    base_url="https://api.siliconflow.com/v1",
                    temperature=0,
                )

    def test_get_llm_client_fireworks(self):
        """Test LLM client factory with Fireworks provider."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "fireworks"
            mock_settings.fireworks_api_key = "test-fw-key"
            mock_settings.fireworks_model = (
                "accounts/fireworks/models/llama-v3p1-8b-instruct"
            )
            mock_settings.fireworks_base_url = "https://api.fireworks.ai/inference/v1"

            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_client = Mock()
                mock_chat.return_value = mock_client

                result = get_llm_client()

                assert result == mock_client
                mock_chat.assert_called_once_with(
                    model="accounts/fireworks/models/llama-v3p1-8b-instruct",
                    api_key="test-fw-key",
                    base_url="https://api.fireworks.ai/inference/v1",
                    temperature=0,
                )

    def test_get_llm_client_unknown_provider(self):
        """Test LLM client factory with unknown provider."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "unknown"

            with pytest.raises(ValueError, match="Unknown LLM_PROVIDER: unknown"):
                get_llm_client()

    def test_get_llm_client_missing_api_key(self):
        """Test LLM client factory with missing API key."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = ""

            with pytest.raises(ValueError, match="Anthropic API key not configured"):
                get_llm_client()

    def test_get_direct_client_anthropic(self):
        """Test direct client factory with Anthropic provider."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "anthropic"
            mock_settings.anthropic_api_key = "test-key"

            with patch("anthropic.Anthropic") as mock_anthropic:
                mock_client = Mock()
                mock_anthropic.return_value = mock_client

                result = get_direct_client()

                assert result == mock_client
                mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_get_direct_client_groq(self):
        """Test direct client factory with Groq provider."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "groq"
            mock_settings.groq_api_key = "test-groq-key"

            with patch("groq.Groq") as mock_groq:
                mock_client = Mock()
                mock_groq.return_value = mock_client

                result = get_direct_client()

                assert result == mock_client
                mock_groq.assert_called_once_with(api_key="test-groq-key")

    def test_get_direct_client_missing_key(self):
        """Test direct client factory with missing API key."""
        with patch("services.llm_client.settings") as mock_settings:
            mock_settings.llm_provider = "groq"
            mock_settings.groq_api_key = ""

            with pytest.raises(ValueError, match="Groq API key not configured"):
                get_direct_client()
