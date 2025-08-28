from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai._types import NotGiven, NOT_GIVEN


class Agent:
    def __init__(
            self,
            agent_name: str,
            client: OpenAI,
            model_name: str,
            system_prompt: str = "",
            tools: list[dict] | NotGiven = NOT_GIVEN
    ) -> None:
        self.agent_name: str = agent_name
        self.client: OpenAI = client
        self.model_name: str = model_name

        self.messages: list[dict] = []
        if system_prompt != "":
            self.messages.append({"role": "system", "content": system_prompt})

        self.tools: list[dict] | NotGiven = tools

    def __call__(self) -> dict:
        response: ChatCompletion = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,  # type: ignore
            tools=self.tools
        )

        message_dict = response.choices[0].message.model_dump()
        self.messages.append(message_dict)

        return message_dict

    def user_call(
            self,
            user_content: str | list[dict],
    ) -> dict:
        self.messages.append({"role": "user", "content": user_content})

        return self()