import json
from datetime import datetime

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QFrame, QLabel, QScrollArea
)
from PySide6.QtGui import QFont, QShortcut, QFontDatabase, QPixmap

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
        tools=edit_mode_tools
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
                    tool = edit_mode_tools_mapping[tool_name]
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


class MessageWidget(QFrame):
    delete_requested = Signal(object)

    def __init__(self, avatar_path, sender, message_content, is_error = False):
        super().__init__()

        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("QFrame { background-color: white; }")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(5)

        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        avatar_label = QLabel()
        avatar_label.setFixedSize(32, 32)
        pixmap = QPixmap(avatar_path)
        avatar_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio))
        header_layout.addWidget(avatar_label)

        info = QLabel()
        info.setText(f"{sender}\n{datetime.now().strftime("%m/%d %H:%M")}")
        header_layout.addWidget(info)

        delete_button = QPushButton("✕")
        delete_button.setFixedSize(26, 26)
        delete_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #CCCCCC
            }
            QPushButton:hover {
                background-color: #FFE6E6;
                color: #FF0000;
            }
        """)
        delete_button.setToolTip("删除这条消息")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self))
        header_layout.addWidget(delete_button)

        main_layout.addWidget(header_container)

        content_label = QLabel()
        content_label.setWordWrap(True)
        if is_error:
            content_label.setStyleSheet("color: #FF0000;")
            content_label.setText(f"错误: {message_content}")
        else:
            content_label.setText(message_content)
        main_layout.addWidget(content_label)

        self.setLayout(main_layout)


class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()

        font_id = QFontDatabase.addApplicationFont('./assets/fonts/TwemojiCountryFlags.ttf')
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        self.font_family = font_families[0]

        layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #FFFFFF}")
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
        self.scroll_area.verticalScrollBar().setStyleSheet(vertical_scrollbar_style)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(0)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_widget)

        layout.addWidget(self.scroll_area)

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

    def insert_message(self, avatar_path, sender, message_content, is_error = False):
        message_widget = MessageWidget(avatar_path, sender, message_content, is_error)
        message_widget.delete_requested.connect(self.delete_message)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, separator)

        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def delete_message(self, message_widget):
        for i in range(self.messages_layout.count()):
            if self.messages_layout.itemAt(i).widget() == message_widget:
                widget_index = i
                break

        self.messages_layout.removeWidget(message_widget)
        message_widget.deleteLater()

        separator = self.messages_layout.itemAt(widget_index).widget()
        self.messages_layout.removeWidget(separator)
        separator.deleteLater()

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