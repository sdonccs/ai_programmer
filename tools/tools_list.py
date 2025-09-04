from tools.file_ops import get_dir_tree, read_file, create_file, edit_file, delete_file_or_dir


tools_list = [
    {
        "type": "function",
        "function": {
            "name": "get_dir_tree",
            "description": "Recursively read the structure of a specified directory and return a string in the form of a directory tree (omitting detailed structures of .git and IDE configuration directories, and excluding __pycache__ directories). Use this tool when you need to understand the structure of an existing directory (e.g., to quickly familiarize yourself with a project, obtain file paths within the project, or when a user requests an operation on a specific file but you don't know its path).",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "The path of the directory to be read (must be an absolute path, please concatenate the path based on the user's project root directory path)"
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
            "description": "Read the entire content of the specified file and return the original content as a string. Use this tool when you need to inspect an existing file but are unaware of its content (e.g., analyzing code, reviewing text files, or extracting information from configuration files). Not suitable for binary files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to be read (must be an absolute path, please concatenate the path based on the user's project root directory path)"
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
            "description": "Create an empty file at the specified path. If the parent directories in the path do not exist, they will be created automatically. Use this tool when you need to create a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to be created (must be an absolute path, please concatenate the path based on the user's project root directory path)"
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
            "description": "Edit the specified file by replacing the old text with new text. Use this tool when you need to edit a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to be edited (must be an absolute path, please concatenate the path based on the user's project root directory path)"
                    },
                    "new_text": {
                        "type": "string",
                        "description": "New text"
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Old text. If this field is left blank (i.e., filled with an \"empty string\"), the new text will completely overwrite all old text in the file"
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
            "description": "Delete the specified file or directory. You can use this tool when you need to delete files or directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file or directory to be deleted (must be an absolute path, please concatenate the path based on the user's project root directory path)"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

tools_mapping = {
    "get_dir_tree": get_dir_tree,
    "read_file": read_file,
    "create_file": create_file,
    "edit_file": edit_file,
    "delete_file_or_dir": delete_file_or_dir,
}