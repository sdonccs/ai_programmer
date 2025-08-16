import os
import shutil


def get_dir_tree(dir_path, show_hidden = True, max_depth = None):
    """
    对应LS工具
    生成标准树形结构的目录显示

    Args:
        dir_path: 目录路径
        show_hidden: 是否显示隐藏文件/目录，通常显示
        max_depth: 最大递归深度，None表示无限制，通常无限制
    """
    # 检查路径是否存在
    if not os.path.exists(dir_path):
        return f"错误：路径 '{dir_path}' 不存在"

    # 检查是否是目录
    if not os.path.isdir(dir_path):
        return f"错误：'{dir_path}' 不是一个目录"

    skip_dirs = {'.git', '.idea', '.vscode'}

    def _build_tree(path, prefix = "", current_depth = 0):
        """递归构建树形结构"""
        if max_depth is not None and current_depth >= max_depth:
            return ""

        tree_str = ""

        try:
            # 获取目录内容
            items = os.listdir(path)

            # 过滤隐藏文件/目录
            if not show_hidden:
                items = [item for item in items if not item.startswith('.')]

            # 分离目录和文件
            dirs = []
            files = []

            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)

            # 排序
            dirs.sort()
            files.sort()

            # 合并目录和文件（目录在前）
            all_items = dirs + files

            for i, item in enumerate(all_items):
                is_last_item = (i == len(all_items) - 1)
                item_path = os.path.join(path, item)

                # 选择合适的树形字符
                if is_last_item:
                    current_prefix = "└── "
                    next_prefix = prefix + "    "
                else:
                    current_prefix = "├── "
                    next_prefix = prefix + "│   "

                # 处理跳过的目录
                if item in skip_dirs and os.path.isdir(item_path):
                    tree_str += f"{prefix}{current_prefix}{item}/\n"
                    tree_str += f"{next_prefix}...\n"
                    continue

                # 显示当前项
                if os.path.isdir(item_path):
                    tree_str += f"{prefix}{current_prefix}{item}/\n"
                    # 递归处理子目录（添加异常处理）
                    if item not in skip_dirs:
                        try:
                            tree_str += _build_tree(item_path, next_prefix, current_depth + 1)
                        except Exception as e:
                            error_prefix = "└── " if is_last_item else "├── "
                            tree_str += f"{next_prefix}{error_prefix}[子目录错误: {str(e)}]\n"
                else:
                    tree_str += f"{prefix}{current_prefix}{item}\n"

        except PermissionError:
            tree_str += f"{prefix}└── [权限被拒绝]\n"
        except Exception as e:
            tree_str += f"{prefix}└── [错误: {str(e)}]\n"

        return tree_str

    # 构建完整的树形结构
    root_name = os.path.basename(os.path.abspath(dir_path))
    if not root_name:  # 处理根目录情况
        root_name = os.path.abspath(dir_path)

    result = f"{root_name}/\n"

    try:
        result += _build_tree(dir_path)
    except Exception as e:
        return f"错误：{str(e)}"

    return result


def read_file(file_path):
    """
    对应View工具
    读取指定文件的全部内容
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return f"错误：文件 '{file_path}' 不存在"

    # 检查是否是文件（而不是目录）
    if not os.path.isfile(file_path):
        return f"错误：'{file_path}' 不是一个文件"

    try:
        # 尝试读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            return f"错误：无法解码文件 '{file_path}'，可能是二进制文件"
    except PermissionError:
        return f"错误：没有权限访问文件 '{file_path}'"
    except Exception as e:
        return f"错误：读取文件时发生错误 - {str(e)}"


def create_file(file_path):
    """
    对应Create工具
    在指定路径创建一个新的空文件
    """
    try:
        # 检查文件是否已存在
        if os.path.exists(file_path):
            return f"错误：文件 '{file_path}' 已存在"

        # 获取目录路径
        dir_path = os.path.dirname(file_path)

        # 如果目录不存在，创建目录
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # 创建空文件
        with open(file_path, 'w', encoding='utf-8') as f:
            pass  # 创建空文件

        return f"成功：文件 '{file_path}' 已创建"

    except PermissionError:
        return f"错误：没有权限在 '{file_path}' 创建文件"
    except Exception as e:
        return f"错误：创建文件时发生错误 - {str(e)}"


def edit_file(file_path, old_text = "", new_text = ""):
    """
    对应Edit工具
    通过用新文本替换旧文本来编辑指定文件
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return f"错误：文件 '{file_path}' 不存在"

    # 检查是否是文件
    if not os.path.isfile(file_path):
        return f"错误：'{file_path}' 不是一个文件"

    try:
        # 读取原文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 如果old_text为空，则完全覆盖文件内容
        if old_text == "":
            new_content = new_text
        else:
            # 替换指定文本
            if old_text not in content:
                return f"错误：在文件中未找到指定的旧文本"
            new_content = content.replace(old_text, new_text)

        # 写入新内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return f"成功：文件 '{file_path}' 已编辑"

    except UnicodeDecodeError:
        return f"错误：无法解码文件 '{file_path}'，可能是二进制文件"
    except PermissionError:
        return f"错误：没有权限编辑文件 '{file_path}'"
    except Exception as e:
        return f"错误：编辑文件时发生错误 - {str(e)}"


def delete_file_or_dir(path):
    """
    对应Delete工具
    删除指定文件或目录
    """
    # 检查路径是否存在
    if not os.path.exists(path):
        return f"错误：路径 '{path}' 不存在"

    try:
        if os.path.isfile(path):
            # 删除文件
            os.remove(path)
            return f"成功：文件 '{path}' 已删除"
        elif os.path.isdir(path):
            # 删除目录及其所有内容
            shutil.rmtree(path)
            return f"成功：目录 '{path}' 已删除"
        else:
            return f"错误：'{path}' 既不是文件也不是目录"

    except PermissionError:
        return f"错误：没有权限删除 '{path}'"
    except Exception as e:
        return f"错误：删除时发生错误 - {str(e)}"