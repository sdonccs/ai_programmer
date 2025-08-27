import json
from datetime import datetime

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPlainTextEdit, QPushButton
)
from PySide6.QtGui import QFont, QTextCursor, QShortcut, QFontDatabase, QTextTableFormat, QTextImageFormat, QTextCharFormat, QColor

from helpers.agent import Agent
from helpers.model_api_client import openrouter_client, openrouter_model_names
from helpers.get_prompt import get_prompt
from tools.tools_list import edit_mode_tools, edit_mode_tools_mapping


class AgentWorker(QObject):
    get_assistant_message_dict = Signal(dict)
    get_tool_result = Signal(str, str)
    finished = Signal()
    error = Signal(str)
    start_work = Signal(str)

    main_agent = Agent(
        agent_name="main_agent",
        client=openrouter_client,
        model_name=openrouter_model_names["moonshotai"][0],
        system_prompt=get_prompt(
            prompt_name="edit_mode_system",
            variables={
                "root_dir_path": "C:/alocation/projects/cherry-studio",
                "cwd_path": "C:/alocation/projects/cherry-studio"
            }
        ),
        tools=edit_mode_tools,
        tools_mapping=edit_mode_tools_mapping
    )

    def __init__(self):
        super().__init__()
        self.start_work.connect(self.run)

    def run(self, user_content):
        try:
            message_dict = AgentWorker.main_agent.user_call(user_content)
            self.get_assistant_message_dict.emit(message_dict)

            assistant_tool_calls = message_dict.get("tool_calls")
            while assistant_tool_calls is not None:
                for assistant_tool_call in assistant_tool_calls:
                    tool_name = assistant_tool_call["function"]["name"]
                    tool = AgentWorker.main_agent.tools_mapping[tool_name]
                    tool_args = json.loads(assistant_tool_call["function"]["arguments"])
                    tool_id = assistant_tool_call["id"]
                    tool_return = tool(**tool_args)
                    tool_content = str(tool_return)

                    AgentWorker.main_agent.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": tool_content
                        }
                    )
                    self.get_tool_result.emit(tool_name, tool_content)
                message_dict = AgentWorker.main_agent()
                self.get_assistant_message_dict.emit(message_dict)

                assistant_tool_calls = message_dict.get("tool_calls")

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()

        font_id = QFontDatabase.addApplicationFont('./assets/fonts/TwemojiCountryFlags.ttf')
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        self.font_family = font_families[0]

        layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        self.chat_display.setStyleSheet("background-color: #FFFFFF;")
        vertical_scrollbar_style = """
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #E6E6E6;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #C8C8C8;
        }

        QScrollBar::handle:vertical:pressed {
            background: #C8C8C8;
        }

        QScrollBar::add-line:vertical {
            height: 0px;
        }

        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
        self.chat_display.verticalScrollBar().setStyleSheet(vertical_scrollbar_style)
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()

        self.input_text = QPlainTextEdit()
        self.input_text.setMaximumHeight(100)
        self.input_text.setPlaceholderText("在这里输入内容，按Ctrl+Enter发送")
        self.input_text.setStyleSheet("background-color: #F3F3F3;")
        font = QFont(f"{self.font_family}")
        font.setPixelSize(14)
        self.input_text.setFont(font)
        input_layout.addWidget(self.input_text)

        self.send_button = QPushButton("发送")
        self.send_button.setMaximumWidth(80)
        self.send_button.clicked.connect(self.send_message)
        short_cut = QShortcut(Qt.CTRL | Qt.Key_Return, self.input_text)
        short_cut.activated.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)

        self.thread = QThread()
        self.agent_worker = AgentWorker()
        self.model_name = self.agent_worker.main_agent.model_name
        self.model_avatar_path = {
            "google/gemini-2.5-pro-preview": "./assets/images/models/gemini.png",
            "anthropic/claude-sonnet-4": "./assets/images/models/claude.png",
            "anthropic/claude-opus-4": "./assets/images/models/claude.png",
            "qwen/qwen3-coder": "./assets/images/models/qwen.png",
            "moonshotai/kimi-k2": "./assets/images/models/kimi.png"
        }[self.model_name]

        self.agent_worker.moveToThread(self.thread)

        self.agent_worker.get_assistant_message_dict.connect(self.on_get_assistant_message_dict)
        self.agent_worker.get_tool_result.connect(self.on_get_tool_result)
        self.agent_worker.finished.connect(self.on_finished)
        self.agent_worker.error.connect(self.on_agent_error)

        self.thread.start()
    def insert_message(self, avatar_path, sender_name, message_content, is_error = False):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 创建表格格式
        table_format = QTextTableFormat()
        table_format.setCellPadding(2)
        table_format.setCellSpacing(0)
        # table_format.setBorderStyle(QTextTableFormat.BorderStyle_Solid)
        # table_format.setBorder(2)
        # table_format.setBorderBrush(QColor("#000000"))
        # table_format.setBorderCollapse(False)


        # 插入表格 (2行2列)
        table = cursor.insertTable(2, 2, table_format)

        # 第一行第一列：插入头像
        cell_00 = table.cellAt(0, 0)
        cell_cursor = cell_00.firstCursorPosition()

        # 插入头像图片
        image_format = QTextImageFormat()
        image_format.setName(avatar_path)
        image_format.setWidth(32)
        image_format.setHeight(32)
        cell_cursor.insertImage(image_format)

        # 第一行第二列：插入发送者名称和时间
        cell_01 = table.cellAt(0, 1)
        cell_cursor = cell_01.firstCursorPosition()

        # 设置粗体格式用于发送者名称
        bold_format = QTextCharFormat()
        font = QFont(f"{self.font_family}")
        font.setPixelSize(14)
        font.setBold(True)
        bold_format.setFont(font)

        cell_cursor.insertText(sender_name, bold_format)
        cell_cursor.insertText("\n")

        # 设置时间格式
        time_format = QTextCharFormat()
        time_format.setForeground(QColor("#A2A2A2"))
        font = QFont(f"{self.font_family}")
        font.setPixelSize(10)
        time_format.setFont(font)

        current_time = datetime.now().strftime("%m/%d %H:%M")
        cell_cursor.insertText(current_time, time_format)

        # 第二行第二列：插入消息内容
        cell_11 = table.cellAt(1, 1)
        cell_cursor = cell_11.firstCursorPosition()

        # 设置消息内容格式
        content_format = QTextCharFormat()
        font = QFont(f"{self.font_family}")
        font.setPixelSize(14)
        content_format.setFont(font)

        if is_error:
            content_format.setForeground(QColor("#FF0000"))
            cell_cursor.insertText(f"错误: {message_content}", content_format)
        else:
            cell_cursor.insertText(message_content, content_format)

        # 移动到表格后面
        cursor.movePosition(QTextCursor.End)

        # 插入分隔线
        cursor.insertHtml("<hr>")

        # 确保滚动到底部
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def send_message(self):
        self.send_button.setEnabled(False)
        self.send_button.setText("处理中……")

        raw = self.input_text.toPlainText()

        if raw.strip() == "":
            self.send_button.setEnabled(True)
            self.send_button.setText("发送")
            return

        self.insert_message("./assets/images/user.png", "用户", raw)

        self.input_text.clear()

        self.agent_worker.start_work.emit(raw)

    def on_get_assistant_message_dict(self, message_dict):
        if message_dict.get("tool_calls") is not None:
            display = f"{message_dict.get('content')}\n<tool_calls>\n{message_dict.get('tool_calls')}\n</tool_calls>"
        else:
            display = f"{message_dict.get('content')}"

        self.insert_message(self.model_avatar_path, self.model_name, display)

    def on_get_tool_result(self, tool_name, tool_content):
        self.insert_message("./assets/images/tool.jpg", tool_name, tool_content)

    def on_finished(self):
        self.send_button.setEnabled(True)
        self.send_button.setText("发送")

    def on_agent_error(self, error_str):
        self.insert_message(self.model_avatar_path, self.model_name, error_str, is_error=True)

        self.send_button.setEnabled(True)
        self.send_button.setText("发送")

    def closeEvent(self, event):
        self.thread.quit()
        self.thread.wait()
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("测试")
        self.setGeometry(500, 150, 600, 800)

        container = QWidget(self)
        self.setCentralWidget(container)

        main_layout = QVBoxLayout(container)

        self.chat_widget = ChatWidget()
        main_layout.addWidget(self.chat_widget)

    def closeEvent(self, event):
        self.chat_widget.closeEvent(event)
        event.accept()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()