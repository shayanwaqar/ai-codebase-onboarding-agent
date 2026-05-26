from app.config import settings


class ChatError(RuntimeError):
    pass


class OpenAIChatService:
    def __init__(
        self,
        api_key: str = settings.openai_api_key,
        model: str = settings.openai_chat_model,
    ) -> None:
        if not api_key:
            raise ChatError("OPENAI_API_KEY is required for answer generation.")

        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def answer(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if not content:
            raise ChatError("OpenAI returned an empty answer.")
        return content.strip()
