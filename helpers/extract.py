import re

from helpers.get_logger import get_logger


logger = get_logger(__name__, 200)


def extract_target_from_content_xml_tag(
        content: str,
        xml_tag: str
) -> str | None:
    pattern = f"<{xml_tag}>\\n(.*?)\\n</{xml_tag}>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        target = match.group(1)
        logger.info(f"提取成功！结果{'-' * 10}\n{target}\n{'-' * 40}")
        return target
    else:
        return None