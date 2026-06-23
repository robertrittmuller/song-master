import os
import unittest
from unittest.mock import patch

from backend.shared.ai_functions import get_llm


class _LiteLLMMessage:
    content = "generated lyrics"


class _LiteLLMChoice:
    message = _LiteLLMMessage()


class _LiteLLMResponse:
    choices = [_LiteLLMChoice()]


class LLMRuntimeConfigTests(unittest.TestCase):
    def test_litellm_uses_extended_timeout_and_thinking_token_budget(self):
        env = {
            "LITELLM_MODEL": "openrouter/deepseek/deepseek-r1",
            "LITELLM_API_KEY": "test-key",
            "LITELLM_API_BASE": "https://openrouter.ai/api/v1",
            "LLM_MAX_TOKENS": "4096",
            "LLM_THINKING_MAX_TOKENS": "12000",
            "LLM_REQUEST_TIMEOUT_SECONDS": "987",
            "LITELLM_TEMPERATURE": "0.2",
        }

        with patch.dict(os.environ, env, clear=False):
            llm = get_llm(use_local=False)

        self.assertEqual(llm.max_tokens, 12000)
        self.assertEqual(llm.request_timeout, 987)
        self.assertEqual(llm.temperature, 0.2)

        with patch("backend.shared.ai_functions.completion", return_value=_LiteLLMResponse()) as completion:
            response = llm.invoke("Write a song.")

        self.assertEqual(response, "generated lyrics")
        completion.assert_called_once()
        call_kwargs = completion.call_args.kwargs
        self.assertEqual(call_kwargs["timeout"], 987)
        self.assertEqual(call_kwargs["max_tokens"], 12000)
        self.assertEqual(call_kwargs["temperature"], 0.2)

    def test_litellm_keeps_standard_token_budget_for_non_thinking_models(self):
        env = {
            "LITELLM_MODEL": "openrouter/openai/gpt-4o-mini",
            "LLM_MAX_TOKENS": "3000",
            "LLM_THINKING_MAX_TOKENS": "12000",
            "LLM_REQUEST_TIMEOUT_SECONDS": "456",
        }

        with patch.dict(os.environ, env, clear=False):
            llm = get_llm(use_local=False)

        self.assertEqual(llm.max_tokens, 3000)
        self.assertEqual(llm.request_timeout, 456)

    def test_local_client_receives_request_timeout(self):
        env = {
            "LMSTUDIO_API_KEY": "lm-studio",
            "LMSTUDIO_BASE_URL": "http://localhost:1234/v1",
            "LMSTUDIO_LLM_MODEL": "qwen/qwen3-30b-a3b-2507",
            "LLM_REQUEST_TIMEOUT_SECONDS": "654",
            "LLM_THINKING_MAX_TOKENS": "11000",
        }

        with patch("backend.shared.ai_functions.openai.OpenAI") as openai_client:
            with patch.dict(os.environ, env, clear=False):
                llm = get_llm(use_local=True)

        self.assertEqual(llm.max_tokens, 11000)
        self.assertEqual(llm.request_timeout, 654)
        openai_client.assert_called_once_with(
            api_key="lm-studio",
            base_url="http://localhost:1234/v1",
            timeout=654,
        )

    def test_langchain_openai_fallback_receives_timeout(self):
        env = {
            "LITELLM_MODEL": "",
            "OPENROUTER_API_KEY": "your_openrouter_api_key_here",
            "OPENAI_API_KEY": "test-openai-key",
            "LLM_MODEL": "openai/gpt-4o-mini",
            "LLM_MAX_TOKENS": "2222",
            "LLM_REQUEST_TIMEOUT_SECONDS": "333",
        }

        with patch("backend.shared.ai_functions.OpenAI") as openai_llm:
            with patch.dict(os.environ, env, clear=False):
                get_llm(use_local=False)

        openai_llm.assert_called_once()
        call_kwargs = openai_llm.call_args.kwargs
        self.assertEqual(call_kwargs["max_tokens"], 2222)
        self.assertEqual(call_kwargs["timeout"], 333)
        self.assertNotIn("request_timeout", call_kwargs)


if __name__ == "__main__":
    unittest.main()
