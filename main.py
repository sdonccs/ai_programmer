import sys

from helpers.agent import Agent
from helpers.model_api_client import openrouter_client, openrouter_model_names
from helpers.get_prompt import get_prompt
from tools.tools_list import edit_mode_tools, edit_mode_tools_mapping


def main():
    # 创建编辑模式Agent
    edit_mode_agent = Agent(
        agent_name="edit_mode_agent",
        client=openrouter_client,
        model_name=openrouter_model_names["qwen"][0],
        system_prompt=get_prompt(
            prompt_name="edit_mode_system",
            variables={
                "root_dir_path": "C:/alocation/projects/cherry-studio",
                "cwd_path": "C:/alocation/projects/cherry-studio",
            }
        ),
        tools=edit_mode_tools,
        tools_mapping=edit_mode_tools_mapping,
    )

    while True:
        # 用户输入内容
        print("请输入内容：")
        user_content = sys.stdin.read()
        if user_content.endswith("\n"):
            user_content = user_content[:-1]

        # 发送用户输入的内容给Agent
        edit_mode_agent.user_call(user_content)

        # 工具调用循环
        edit_mode_agent.tool_calling_loop()


if __name__ == "__main__":
    main()