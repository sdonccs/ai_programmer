from pathlib import Path


def get_prompt(
        prompt_name: str,
        variables: dict[str, str] | None = None,
        prompts_dir_path: str | Path = "./prompts",
) -> str:
    prompts_dir = Path(prompts_dir_path)

    prompt_file_path = prompts_dir / f"{prompt_name}.txt"
    try:
        with open(prompt_file_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"提示词文件 \"{prompt_file_path}\" 不存在。")
    if variables is None:
        return prompt_template

    for variable_name in variables:
        prompt_template = prompt_template.replace(f"${{{variable_name}}}", variables[variable_name])
    return prompt_template