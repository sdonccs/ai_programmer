import json
import uuid
from datetime import datetime

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QFrame, QLabel, QScrollArea, QTextBrowser
)
from PySide6.QtGui import QFont, QShortcut, QFontDatabase, QPixmap

from helpers.agent import Agent
from helpers.model_api_client import openrouter_client, openrouter_model_names
from helpers.get_prompt import get_prompt
from tools.tools_list import tools_list, tools_mapping


vertical_scrollBar_style_sheet = """
QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    margin: 0px;
}
QScrollBar::track:vertical {
    background-color: transparent;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background-color: transparent;
}
QScrollBar::handle:vertical {
    background-color: #E6E6E6;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #C8C8C8;
}
QScrollBar::handle:vertical:pressed {
    background-color: #C8C8C8;
}
QScrollBar::add-line:vertical {
    height: 0px;
}
QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def load_font():
    font_id = QFontDatabase.addApplicationFont('./assets/fonts/TwemojiCountryFlags.ttf')
    font_families = QFontDatabase.applicationFontFamilies(font_id)
    return font_families[0]


class AgentWorker(QObject):
    get_assistant_message_dict = Signal(object, dict)
    get_tool_result = Signal(object, str, str)
    finished = Signal()
    get_message_id = Signal(object, int)
    start_work = Signal(str)

    main_agent = Agent(
        agent_name="main_agent",
        client=openrouter_client,
        model_name=openrouter_model_names["anthropic"][0],
        system_prompt=get_prompt(
            prompt_name="main_system",
            variables={
                "root_dir_path": "C:/alocation/projects/cherry-studio",
                "cwd_path": "C:/alocation/projects/cherry-studio"
            }
        ),
        tools=tools_list
    )

    def __init__(self):
        super().__init__()
        self.start_work.connect(self.run)

    def run(self, user_content):
        message_dict = AgentWorker.main_agent.user_call(user_content)
        assistant_message_id = uuid.uuid4()
        assistant_message_index = len(AgentWorker.main_agent.messages) - 1
        self.get_message_id.emit(assistant_message_id, assistant_message_index)
        self.get_assistant_message_dict.emit(assistant_message_id, message_dict)

        assistant_tool_calls = message_dict.get("tool_calls")
        while assistant_tool_calls is not None:
            for assistant_tool_call in assistant_tool_calls:
                tool_name = assistant_tool_call["function"]["name"]
                tool = tools_mapping[tool_name]
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
                tool_message_id = uuid.uuid4()
                tool_message_index = len(AgentWorker.main_agent.messages) - 1
                self.get_message_id.emit(tool_message_id, tool_message_index)

                self.get_tool_result.emit(tool_message_id, tool_name, tool_content)
            message_dict = AgentWorker.main_agent()
            assistant_message_id = uuid.uuid4()
            assistant_message_index = len(AgentWorker.main_agent.messages) - 1
            self.get_message_id.emit(assistant_message_id, assistant_message_index)
            self.get_assistant_message_dict.emit(assistant_message_id, message_dict)

            assistant_tool_calls = message_dict.get("tool_calls")

        self.finished.emit()


class MessageContentWidget(QTextBrowser):
    def __init__(self):
        super().__init__()

        self.font_family = load_font()

        self.document().documentLayout().documentSizeChanged.connect(self.on_document_size_changed)

        font = QFont(self.font_family)
        font.setPixelSize(14)
        self.setFont(font)
        style_sheet = """
QTextBrowser {
    background-color: transparent; 
    border: none;
}
"""
        self.setStyleSheet(style_sheet)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def on_document_size_changed(self, new_size):
        self.setFixedHeight(int(new_size.height()))


class MessageReasoningWidget(QTextBrowser):
    def __init__(self):
        super().__init__()

        self.font_family = load_font()

        self.setFixedHeight(100)
        font = QFont(self.font_family)
        font.setPixelSize(14)
        self.setFont(font)
        style_sheet = f"""
QTextBrowser {{
    background-color: transparent; 
    border: 1px solid gray;
}}

{vertical_scrollBar_style_sheet}
"""
        self.setStyleSheet(style_sheet)


class MessageWidget(QFrame):
    delete_requested = Signal(object, object)

    def __init__(self, message_id, avatar_path, sender, message_content, markdown_rendering, reasoning = None, tool_calls = None):
        super().__init__()

        self.font_family = load_font()

        self.message_id = message_id

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
        avatar_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(avatar_label)

        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        sender_name = QLabel()
        font = QFont(self.font_family)
        font.setPixelSize(14)
        sender_name.setFont(font)
        sender_name.setStyleSheet("font-weight: bold")
        sender_name.setText(sender)
        info_layout.addWidget(sender_name)

        time_info = QLabel()
        font = QFont(self.font_family)
        font.setPixelSize(10)
        time_info.setFont(font)
        time_info.setStyleSheet("color: #A0A0A0")
        time_info.setText(datetime.now().strftime("%m/%d %H:%M"))
        info_layout.addWidget(time_info)

        header_layout.addWidget(info_container)

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
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.message_id, self))
        header_layout.addWidget(delete_button)

        main_layout.addWidget(header_container)

        if reasoning is not None:
            reasoning_display = MessageReasoningWidget()
            reasoning_display.setPlainText(reasoning)
            main_layout.addWidget(reasoning_display)

        content_display = MessageContentWidget()
        # 暂时放弃markdown渲染
        if markdown_rendering == True:
            content_display.setPlainText(message_content)
        elif markdown_rendering == False:
            content_display.setPlainText(message_content)
        main_layout.addWidget(content_display)

        self.setLayout(main_layout)


class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.font_family = load_font()

        layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_area_style_sheet = f"""
QScrollArea {{
    background-color: #FFFFFF;
}}

{vertical_scrollBar_style_sheet}
"""
        self.scroll_area.setStyleSheet(scroll_area_style_sheet)

        self.messages_display = QWidget()
        self.messages_display.setStyleSheet("background-color: #FFFFFF")
        self.messages_layout = QVBoxLayout(self.messages_display)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(0)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_display)

        layout.addWidget(self.scroll_area)

        input_layout = QHBoxLayout()

        self.input_text = QPlainTextEdit()
        self.input_text.setFixedHeight(100)
        self.input_text.setPlaceholderText("在这里输入内容，按Ctrl+Enter发送")
        input_text_style_sheet = f"""
QPlainTextEdit {{
    background-color: #F3F3F3;
}}

{vertical_scrollBar_style_sheet}
"""
        self.input_text.setStyleSheet(input_text_style_sheet)
        font = QFont(self.font_family)
        font.setPixelSize(14)
        self.input_text.setFont(font)
        input_layout.addWidget(self.input_text)

        self.send_button = QPushButton("发送")
        font = QFont(self.font_family)
        font.setPixelSize(14)
        self.send_button.setFont(font)
        self.send_button.setFixedSize(50, 100)
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
        self.agent_worker.get_message_id.connect(self.on_get_message_id)
        self.id_to_index_mapping = {}

        self.thread.start()

    def on_get_message_id(self, message_uid, message_index):
        self.id_to_index_mapping[message_uid] = message_index
        # print(self.id_to_index_mapping)

    def insert_message(self, message_id, avatar_path, sender, message_content, markdown_rendering, reasoning):
        message_widget = MessageWidget(message_id, avatar_path, sender, message_content, markdown_rendering, reasoning)
        message_widget.delete_requested.connect(self.delete_message)

        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget, 0, Qt.AlignTop)

    def delete_message(self, message_id ,message_widget):
        deleted_index = self.id_to_index_mapping[message_id]
        del self.agent_worker.main_agent.messages[deleted_index]
        del self.id_to_index_mapping[message_id]
        for id, index in self.id_to_index_mapping.items():
            if index > deleted_index:
                self.id_to_index_mapping[id] = index - 1

        self.messages_layout.removeWidget(message_widget)
        message_widget.deleteLater()

    def send_message(self):
        self.send_button.setEnabled(False)

        raw = self.input_text.toPlainText()

        if raw.strip() == "":
            self.send_button.setEnabled(True)
            return

        user_message_id = uuid.uuid4()
        user_message_index = len(self.agent_worker.main_agent.messages)
        self.on_get_message_id(user_message_id, user_message_index)

        self.insert_message(user_message_id, "./assets/images/user.png", "用户", raw, False, None)

        self.input_text.clear()

        self.agent_worker.start_work.emit(raw)

    def on_get_assistant_message_dict(self, message_id, message_dict):
        if message_dict.get("tool_calls") is not None:
            display = f"{message_dict.get('content')}\n{message_dict.get('tool_calls')}"
        else:
            display = f"{message_dict.get('content')}"
        reasoning = message_dict.get("reasoning")
        # print(message_dict)
        self.insert_message(message_id, self.model_avatar_path, self.model_name, display, True, reasoning)

    def on_get_tool_result(self, message_id, tool_name, tool_content):
        self.insert_message(message_id, "./assets/images/tool.jpg", tool_name, tool_content, False, None)

    def on_finished(self):
        self.send_button.setEnabled(True)

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