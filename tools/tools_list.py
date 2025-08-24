from tools.file_ops import get_dir_tree, read_file, create_file, edit_file, delete_file_or_dir


edit_mode_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_dir_tree",
            "description": "递归读取指定目录的结构，返回目录树形式的字符串（省略了.git、IDE配置目录的详细结构，不会显示__pycache__目录）。当你需要了解现有目录的结构时（例如快速了解项目，获得项目中文件的路径），可使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "要读取的目录的路径（必须是绝对路径，请以用户项目根目录路径为基础来拼接路径）"
                    }
                },
                "required": ["dir_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文件的全部内容，返回文件原始内容的字符串。当你需要检查现有文件但不知其内容时（例如分析代码、审阅文本文件或从配置文件中提取信息），可使用此工具。不适用于二进制文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要读取的文件的路径（必须是绝对路径，请以用户项目根目录路径为基础来拼接路径）"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "在指定路径创建一个空文件。如果路径中的父目录不存在，会自动创建。当你需要创建文件时，可使用此工具。调用此工具前，请先询问用户。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要创建的文件的路径（必须是绝对路径，请以用户项目根目录路径为基础来拼接路径）"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "通过用新文本替换旧文本来编辑指定的文件。当你需要编辑文件时，可使用此工具。调用此工具前，请先询问用户。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要编辑的文件的路径（必须是绝对路径，请以用户项目根目录路径为基础来拼接路径）"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "新文本"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "旧文本，如果此项留空（即填“空字符串”），则会用新文本完全覆盖文件中所有的旧文本"
                    }
                },
                "required": ["file_path", "new_text", "old_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file_or_dir",
            "description": "删除指定的文件或目录。当你需要删除文件或目录时，可使用此工具。调用此工具前，请先询问用户。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要删除的文件或目录的路径（必须是绝对路径，请以用户项目根目录路径为基础来拼接路径）"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

edit_mode_tools_mapping = {
    "get_dir_tree": get_dir_tree,
    "read_file": read_file,
    "create_file": create_file,
    "edit_file": edit_file,
    "delete_file_or_dir": delete_file_or_dir,
}