from openai import OpenAI
from openai.types.chat import ChatCompletion

from helpers.get_logger import get_logger


logger = get_logger(__name__, 8000)


class Agent:
    def __init__(
            self,
            client: OpenAI,
            model_name: str,
            system_prompt: str = "",
            agent_name: str = "",
    ) -> None:
        self.client: OpenAI = client
        self.model_name: str = model_name

        self.messages: list = []
        if system_prompt != "":
            self.messages.append({"role": "system", "content": system_prompt})
            logger.info(f"[system_prompt] [{self.model_name}]\n{system_prompt}\n{'-' * 70}")

        self.agent_name: str = agent_name

    def get_content(
            self,
            user_prompt: str | list[dict],
    ) -> str:
        self.messages.append({"role": "user", "content": user_prompt})
        logger.info(f"[user_prompt] [{self.model_name}]\n{user_prompt}\n{'-' * 70}")

        response: ChatCompletion = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages  # type: ignore
        )

        content: str = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": content})
        logger.info(f"[content] [{self.model_name}]\n{content}\n{'-' * 70}")

        return content