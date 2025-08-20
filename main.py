import sys
import json

from helpers.agent import Agent
from helpers.model_api_client import openrouter_client, openrouter_model_names
from helpers.get_prompt import get_prompt
from helpers.extract import extract_target_from_content_xml_tag
from tools.file_ops import get_dir_tree, read_file, create_file, edit_file, delete_file_or_dir


# 工具名-实际标识符映射字典
tools_map_dict = {
    "LS": get_dir_tree,
    "View": read_file,
    "Create": create_file,
    "Edit": edit_file,
    "Delete": delete_file_or_dir
}


# 主函数
def main():
    # 提示词中必要的变量
    variables = {
        "root_dir_path": "C:/alocation/projects/cherry-studio",
        "cwd_path": "C:/alocation/projects/cherry-studio",
    }

    # 选择模式
    while True:
        mode = input("请选择模式：1（ask模式）/2（edit模式）/3（questionnaire模式）：")
        if mode == "1":
            model_name = openrouter_model_names["google"][0]
            system_prompt = get_prompt(
                prompt_name="ask_mode_system",
                variables=variables
            )
            break
        elif mode == "2":
            model_name = openrouter_model_names["anthropic"][0]
            system_prompt = get_prompt(
                prompt_name="edit_mode_system",
                variables=variables
            )
            break
        elif mode == "3":
            model_name = openrouter_model_names["google"][0]
            system_prompt = get_prompt(
                prompt_name="questionnaire_mode_system",
                variables=variables
            )
            break
        else:
            print("请输入数字：1/2/3。")

    # 创建主Agent
    main_agent = Agent(
        client=openrouter_client,
        model_name=model_name,
        system_prompt=system_prompt
    )

    # 对话循环
    while True:
        # 用户输入内容
        print("请输入内容：")
        user_prompt = sys.stdin.read()
        if user_prompt.endswith("\n"):
            user_prompt = user_prompt[:-1]

        # 用户输入“/shift”则切换模型
        if user_prompt == "/shift":
            if main_agent.model_name == openrouter_model_names["google"][0]:
                main_agent.model_name = openrouter_model_names["anthropic"][0]
            elif main_agent.model_name == openrouter_model_names["anthropic"][0]:
                main_agent.model_name = openrouter_model_names["google"][0]
            print(f"已切换模型为{main_agent.model_name}")
            continue

        # 发送用户输入的内容给主Agent，并获得回复内容
        content = main_agent.get_content(user_prompt)

        # 提取工具调用信息
        tool_calling = extract_target_from_content_xml_tag(content, "tool_calling")

        # 如果提取工具调用信息成功则进入工具调用循环
        while tool_calling is not None:
            # 询问用户是否确认执行
            is_exc = input("是否执行工具调用？（y/n）")

            # 用户输入“/shift”则切换模型
            if is_exc == "/shift":
                if main_agent.model_name == openrouter_model_names["google"][0]:
                    main_agent.model_name = openrouter_model_names["anthropic"][0]
                elif main_agent.model_name == openrouter_model_names["anthropic"][0]:
                    main_agent.model_name = openrouter_model_names["google"][0]
                print(f"已切换模型为{main_agent.model_name}")
                continue

            # 用户输入“y”则执行工具调用
            if is_exc == "y":
                # 将工具调用信息转换为字典
                tool_calling_dict = json.loads(tool_calling)
                # 获得工具名对应的实际标识符
                tool = tools_map_dict[tool_calling_dict["tool_name"]]
                # 传入参数调用工具，获得返回值
                tool_return = tool(**tool_calling_dict["parameters"])
                # 格式化工具返回值
                tool_return_message = f"""<tool_return>
{tool_return}
</tool_return>"""
                # 将格式化后的工具返回值发送给主Agent，并获得回复内容
                content = main_agent.get_content(tool_return_message)

                # 再次提取工具调用信息
                tool_calling = extract_target_from_content_xml_tag(content, "tool_calling")
            else:
                # 用户拒绝执行工具调用则退出工具调用循环
                break


# 程序入口
if __name__ == "__main__":
    main()