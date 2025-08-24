import json
from typing import Callable

from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai._types import NotGiven, NOT_GIVEN

from helpers.get_logger import get_logger


logger = get_logger(__name__, 8000)


class Agent:
    def __init__(
            self,
            agent_name: str,
            client: OpenAI,
            model_name: str,
            system_prompt: str = "",
            tools: list[dict] | NotGiven = NOT_GIVEN,
            tools_mapping: dict[str, Callable] | None = None
    ) -> None:
        self.agent_name: str = agent_name
        self.client: OpenAI = client
        self.model_name: str = model_name

        self.messages: list[dict] = []
        if system_prompt != "":
            self.messages.append({"role": "system", "content": system_prompt})
            logger.info(f"[{self.agent_name}] [{self.model_name}] [message{len(self.messages)}] [system] [(content)\n{system_prompt}\n]{'='*70}")

        self.tools: list[dict] | NotGiven = tools
        self.tools_mapping: dict[str, Callable] | None = tools_mapping

    def __call__(self) -> dict:
        response: ChatCompletion = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,  # type: ignore
            tools=self.tools
        )

        message_dict = response.choices[0].message.model_dump()
        self.messages.append(message_dict)

        assistant_reasoning = message_dict.get("reasoning")
        if assistant_reasoning is not None:
            logger.info(f"[{self.agent_name}] [{self.model_name}] [message{len(self.messages)}] [assistant] [(reasoning)\n{assistant_reasoning}\n]{'='*70}")

        assistant_content = message_dict.get("content")
        logger.info(f"[{self.agent_name}] [{self.model_name}] [message{len(self.messages)}] [assistant] [(content)\n{assistant_content}\n]{'='*70}")

        assistant_tool_calls = message_dict.get("tool_calls")
        if assistant_tool_calls is not None:
            logger.info(f"[{self.agent_name}] [{self.model_name}] [message{len(self.messages)}] [assistant] [(tool_calls)\n{assistant_tool_calls}\n]{'='*70}")

        return message_dict

    def user_call(
            self,
            user_content: str | list[dict],
    ) -> dict:
        self.messages.append({"role": "user", "content": user_content})
        logger.info(f"[{self.agent_name}] [{self.model_name}] [message{len(self.messages)}] [user] [(content)\n{user_content}\n]{'='*70}")

        return self()

    def tool_calling_loop(self) -> dict:
        assistant_tool_calls = self.messages[-1].get("tool_calls")
        while assistant_tool_calls is not None:
            for assistant_tool_call in assistant_tool_calls:
                tool = self.tools_mapping[assistant_tool_call["function"]["name"]]
                tool_args = json.loads(assistant_tool_call["function"]["arguments"])
                tool_id = assistant_tool_call["id"]
                tool_return = tool(**tool_args)
                tool_content = json.dumps(tool_return, ensure_ascii=False)

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": tool_content
                    }
                )
                logger.info(f"[{self.agent_name}] [{self.model_name}] [message{len(self.messages)}] [tool] [(tool_call_id){tool_id}] [(content)\n{tool_content}\n]{'='*70}")
            self()
            assistant_tool_calls = self.messages[-1].get("tool_calls")

        return self.messages[-1]