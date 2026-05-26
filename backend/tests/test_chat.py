import pytest

from app.chat import ChatError, OpenAIChatService


def test_openai_chat_service_requires_api_key() -> None:
    with pytest.raises(ChatError):
        OpenAIChatService(api_key="")
