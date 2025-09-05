import json
import uuid
from datetime import datetime

from PySide6.QtCore import Qt, QObject, QThread, Signal, QSize
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QFrame, QLabel, QScrollArea, QTextBrowser
)
from PySide6.QtGui import QFont, QShortcut, QFontDatabase, QIcon, QInputMethodEvent

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


font_family_name = "Microsoft YaHei"

def load_font():
    font_files = [
        "./assets/fonts/msyhl.ttc",  # 微软雅黑 Light
        "./assets/fonts/msyh.ttc",  # 微软雅黑 Regular
        "./assets/fonts/msyhbd.ttc"  # 微软雅黑 Bold
    ]

    for font_file in font_files:
        QFontDatabase.addApplicationFont(font_file)

    # styles = QFontDatabase.styles(font_family_name)
    # print(f"  可用样式: {styles}")


class CustomPlainTextEdit(QPlainTextEdit):
    """自定义输入框，解决拼音输入法时占位符不消失的问题"""
    
    # 自定义信号，用于通知输入状态变化
    input_state_changed = Signal(bool)  # True表示有效输入，False表示无效输入
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_preedit = False
        self._original_placeholder = ""
        
        # 连接文本变化信号
        self.textChanged.connect(self._check_input_state)
    
    def setPlaceholderText(self, text):
        """重写设置占位符文本的方法"""
        self._original_placeholder = text
        super().setPlaceholderText(text)
    
    def _check_input_state(self):
        """检查输入状态并发送信号"""
        # 只有当没有预编辑文本且输入框不为空时，才认为是有效输入
        has_valid_input = not self._has_preedit and self.toPlainText().strip() != ""
        self.input_state_changed.emit(has_valid_input)
    
    def inputMethodEvent(self, event: QInputMethodEvent):
        """处理输入法事件"""
        # 获取预编辑文本
        preedit_string = event.preeditString()
        
        # 如果有预编辑文本，隐藏占位符
        if preedit_string:
            if not self._has_preedit:
                self._has_preedit = True
                super().setPlaceholderText("")  # 隐藏占位符
                self._check_input_state()  # 检查输入状态
        else:
            # 如果没有预编辑文本且输入框为空，显示占位符
            if self._has_preedit:
                self._has_preedit = False
                if self.toPlainText() == "":
                    super().setPlaceholderText(self._original_placeholder)
                self._check_input_state()  # 检查输入状态
        
        # 调用父类方法处理输入法事件
        super().inputMethodEvent(event)
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        super().keyPressEvent(event)
        
        # 如果没有预编辑文本，根据文本内容决定是否显示占位符
        if not self._has_preedit:
            if self.toPlainText() == "":
                super().setPlaceholderText(self._original_placeholder)
            else:
                super().setPlaceholderText("")


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
                "root_dir_path": "C:/alocation/projects/ai_programmer",
                "cwd_path": "C:/alocation/projects/ai_programmer"
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

        self.document().documentLayout().documentSizeChanged.connect(self.on_document_size_changed)

        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Normal)
        self.setFont(font)
        style_sheet = """
QTextBrowser {
    background-color: #FFFFFF; 
    border: none;
}
"""
        self.setStyleSheet(style_sheet)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def on_document_size_changed(self, new_size):
        self.setFixedHeight(int(new_size.height()))


class MessageReasoningWidget(QWidget):
    def __init__(self):
        super().__init__()

        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Normal)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toggle_button = QPushButton("思考内容")
        self.toggle_button.setLayoutDirection(Qt.RightToLeft)
        self.toggle_button.setIcon(QIcon("assets/images/icon/message_expand.svg"))
        self.toggle_button.setIconSize(QSize(24, 24))
        self.toggle_button.setFont(font)
        self.toggle_button.setFixedHeight(28)
        self.toggle_button_style_sheet = """
QPushButton {
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    background-color: #FFFFFF;
    text-align: left;
    padding: 6px
}
"""
        self.expanded_toggle_button_style_sheet = """
QPushButton {
    border-top: 1px solid #d9d9d9;
    border-right: 1px solid #d9d9d9;
    border-bottom: none;
    border-left: 1px solid #d9d9d9;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 0;
    border-bottom-left-radius: 0;
    background-color: #FFFFFF;
    text-align: left;
    padding: 6px
}
"""
        self.toggle_button.setStyleSheet(self.toggle_button_style_sheet)
        self.toggle_button.clicked.connect(self.toggle_content)
        main_layout.addWidget(self.toggle_button)

        self.content_widget = QTextBrowser()
        self.content_widget.setFont(font)
        self.content_widget.setFixedHeight(100)
        content_widget_style_sheet = f"""
QTextBrowser {{
    background-color: #FFFFFF; 
    border: 1px solid #d9d9d9;
}}

{vertical_scrollBar_style_sheet}
"""
        self.content_widget.setStyleSheet(content_widget_style_sheet)

        self.content_widget.hide()
        self.is_expanded = False
        main_layout.addWidget(self.content_widget)

        self.setLayout(main_layout)

    def toggle_content(self):
        if self.is_expanded:
            self.content_widget.hide()
            self.toggle_button.setText("思考内容")
            self.toggle_button.setIcon(QIcon("assets/images/icon/message_expand.svg"))
            self.toggle_button.setIconSize(QSize(24, 24))
            self.toggle_button.setStyleSheet(self.toggle_button_style_sheet)
            self.is_expanded = False
        else:
            self.content_widget.show()
            self.toggle_button.setText("思考内容")
            self.toggle_button.setIcon(QIcon("assets/images/icon/message_expanded_down.svg"))
            self.toggle_button.setIconSize(QSize(24, 24))
            self.toggle_button.setStyleSheet(self.expanded_toggle_button_style_sheet)
            self.is_expanded = True


class MessageToolsCallWidget(QWidget):
    def __init__(self):
        super().__init__()

        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Normal)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toggle_button = QPushButton("工具调用")
        self.toggle_button.setLayoutDirection(Qt.RightToLeft)
        self.toggle_button.setIcon(QIcon("assets/images/icon/message_expand.svg"))
        self.toggle_button.setIconSize(QSize(24, 24))
        self.toggle_button.setFont(font)
        self.toggle_button.setFixedHeight(28)
        self.toggle_button_style_sheet = """
QPushButton {
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    background-color: #FFFFFF;
    text-align: left;
    padding: 6px
}
"""
        self.expanded_toggle_button_style_sheet = """
QPushButton {
    border-top: 1px solid #d9d9d9;
    border-right: 1px solid #d9d9d9;
    border-bottom: none;
    border-left: 1px solid #d9d9d9;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 0;
    border-bottom-left-radius: 0;
    background-color: #FFFFFF;
    text-align: left;
    padding: 6px
}
"""
        self.toggle_button.setStyleSheet(self.toggle_button_style_sheet)
        self.toggle_button.clicked.connect(self.toggle_content)
        main_layout.addWidget(self.toggle_button)

        self.content_widget = QTextBrowser()
        self.content_widget.setFont(font)
        self.content_widget.setFixedHeight(100)
        content_widget_style_sheet = f"""
QTextBrowser {{
    background-color: #FFFFFF; 
    border: 1px solid #d9d9d9;
}}

{vertical_scrollBar_style_sheet}
"""
        self.content_widget.setStyleSheet(content_widget_style_sheet)

        self.content_widget.hide()
        self.is_expanded = False
        main_layout.addWidget(self.content_widget)

        self.setLayout(main_layout)

    def toggle_content(self):
        if self.is_expanded:
            self.content_widget.hide()
            self.toggle_button.setText("工具调用")
            self.toggle_button.setIcon(QIcon("assets/images/icon/message_expand.svg"))
            self.toggle_button.setIconSize(QSize(24, 24))
            self.toggle_button.setStyleSheet(self.toggle_button_style_sheet)
            self.is_expanded = False
        else:
            self.content_widget.show()
            self.toggle_button.setText("工具调用")
            self.toggle_button.setIcon(QIcon("assets/images/icon/message_expanded_down.svg"))
            self.toggle_button.setIconSize(QSize(24, 24))
            self.toggle_button.setStyleSheet(self.expanded_toggle_button_style_sheet)
            self.is_expanded = True


class ToolMessageWidget(QWidget):
    def __init__(self):
        super().__init__()

        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Normal)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.toggle_button = QPushButton("工具返回")
        self.toggle_button.setLayoutDirection(Qt.RightToLeft)
        self.toggle_button.setIcon(QIcon("assets/images/icon/message_expand.svg"))
        self.toggle_button.setIconSize(QSize(24, 24))
        self.toggle_button.setFont(font)
        self.toggle_button.setFixedHeight(28)
        self.toggle_button_style_sheet = """
QPushButton {
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    background-color: #FFFFFF;
    text-align: left;
    padding: 6px
}
"""
        self.expanded_toggle_button_style_sheet = """
QPushButton {
    border-top: 1px solid #d9d9d9;
    border-right: 1px solid #d9d9d9;
    border-bottom: none;
    border-left: 1px solid #d9d9d9;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 0;
    border-bottom-left-radius: 0;
    background-color: #FFFFFF;
    text-align: left;
    padding: 6px
}
"""
        self.toggle_button.setStyleSheet(self.toggle_button_style_sheet)
        self.toggle_button.clicked.connect(self.toggle_content)
        main_layout.addWidget(self.toggle_button)

        self.content_widget = QTextBrowser()
        self.content_widget.setFont(font)
        self.content_widget.setFixedHeight(100)
        content_widget_style_sheet = f"""
QTextBrowser {{
    background-color: #FFFFFF; 
    border: 1px solid #d9d9d9;
}}

{vertical_scrollBar_style_sheet}
"""
        self.content_widget.setStyleSheet(content_widget_style_sheet)

        self.content_widget.hide()
        self.is_expanded = False
        main_layout.addWidget(self.content_widget)

        self.setLayout(main_layout)

    def toggle_content(self):
        if self.is_expanded:
            self.content_widget.hide()
            self.toggle_button.setText("工具返回")
            self.toggle_button.setIcon(QIcon("assets/images/icon/message_expand.svg"))
            self.toggle_button.setIconSize(QSize(24, 24))
            self.toggle_button.setStyleSheet(self.toggle_button_style_sheet)
            self.is_expanded = False
        else:
            self.content_widget.show()
            self.toggle_button.setText("工具返回")
            self.toggle_button.setIcon(QIcon("assets/images/icon/message_expanded_down.svg"))
            self.toggle_button.setIconSize(QSize(24, 24))
            self.toggle_button.setStyleSheet(self.expanded_toggle_button_style_sheet)
            self.is_expanded = True


class MessageWidget(QFrame):
    delete_requested = Signal(object, object)

    def __init__(
            self,
            message_id,
            avatar_path,
            sender,
            message_content,
            reasoning = None,
            tool_calls = None
    ):
        super().__init__()

        self.message_id = message_id

        self.setStyleSheet("""
QFrame {
    border: none;
    background-color: #FFFFFF;
}
""")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        header_container = QWidget()
        header_container.setFixedHeight(38)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        avatar_svg = QSvgWidget(avatar_path)
        avatar_svg.setFixedSize(35, 35)
        header_layout.addWidget(avatar_svg)

        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(0)

        sender_name = QLabel()
        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Bold)
        sender_name.setFont(font)
        sender_name.setText(sender)
        info_layout.addWidget(sender_name)

        info_layout.addStretch()

        time_info = QLabel()
        font = QFont(font_family_name)
        font.setPixelSize(10)
        font.setWeight(QFont.Weight.Normal)
        time_info.setFont(font)
        time_info.setStyleSheet("color: #A0A0A0")
        time_info.setText(datetime.now().strftime("%m/%d %H:%M"))
        info_layout.addWidget(time_info)

        header_layout.addWidget(info_container)

        header_layout.addStretch()

        delete_button = QPushButton("✕")
        delete_button.setFixedSize(26, 26)
        delete_button.setStyleSheet("""
QPushButton {
    border: none;
    background-color: #FFFFFF;
    color: #CCCCCC
}
QPushButton:hover {
    background-color: #FFE6E6;
    color: #FF0000;
}
QPushButton:pressed {
    background-color: #ffccc7;
    color: #d9363e;
}
""")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.message_id, self))
        header_layout.addWidget(delete_button)

        main_layout.addWidget(header_container)

        if sender in tools_mapping:
            tool_content_display = ToolMessageWidget()
            tool_content_display.content_widget.setPlainText(message_content)
            main_layout.addWidget(tool_content_display)
        else:
            if reasoning is not None:
                reasoning_display = MessageReasoningWidget()
                reasoning_display.content_widget.setPlainText(reasoning)
                main_layout.addWidget(reasoning_display)

            if message_content != "":
                content_display = MessageContentWidget()
                content_display.setPlainText(message_content)
                main_layout.addWidget(content_display)

            if tool_calls is not None:
                tools_calls_display = MessageToolsCallWidget()
                tools_calls_display.content_widget.setPlainText(str(tool_calls))
                main_layout.addWidget(tools_calls_display)

        self.setLayout(main_layout)


class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_area_style_sheet = f"""
QScrollArea {{
    border: none;
    background-color: #FFFFFF;
}}

{vertical_scrollBar_style_sheet}
"""
        self.scroll_area.setStyleSheet(scroll_area_style_sheet)

        self.messages_display = QWidget()
        self.messages_display.setStyleSheet("""
QWidget {
    background-color: #FFFFFF;
}
""")
        self.messages_layout = QVBoxLayout(self.messages_display)
        self.messages_layout.setContentsMargins(5, 5, 5, 5)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_display)

        main_layout.addWidget(self.scroll_area)

        # 操作按钮栏
        self.action_bar = QWidget()
        self.action_bar.setFixedHeight(40)
        action_bar_layout = QHBoxLayout(self.action_bar)
        action_bar_layout.setContentsMargins(0, 5, 0, 5)
        action_bar_layout.setSpacing(10)
        
        self.clear_messages_button = QPushButton("清空消息")
        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Normal)
        self.clear_messages_button.setFont(font)
        self.clear_messages_button.setFixedHeight(30)
        clear_button_style_sheet = """
QPushButton {
    border-radius: 6px;
    background-color: #ffffff;
    color: #ff4d4f;
    padding: 4px 12px;
}
QPushButton:hover {
    background-color: #fff2f0;
    border-color: #ff7875;
    color: #ff7875;
}
QPushButton:pressed {
    background-color: #ffccc7;
    border-color: #d9363e;
    color: #d9363e;
}
"""
        self.clear_messages_button.setStyleSheet(clear_button_style_sheet)
        self.clear_messages_button.clicked.connect(self.clear_messages)
        action_bar_layout.addWidget(self.clear_messages_button)

        action_bar_layout.addStretch()
        
        self.action_bar.hide()  # 初始隐藏
        self.is_action_bar_expanded = False
        main_layout.addWidget(self.action_bar)

        input_layout = QHBoxLayout()

        self.input_text = CustomPlainTextEdit()
        self.input_text.setFixedHeight(100)
        self.input_text.setPlaceholderText("在这里输入内容，按Ctrl+Enter发送")
        input_text_style_sheet = f"""
QPlainTextEdit {{
    background-color: #F3F3F3;
}}

{vertical_scrollBar_style_sheet}
"""
        self.input_text.setStyleSheet(input_text_style_sheet)
        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Normal)
        self.input_text.setFont(font)
        
        # 连接输入状态变化信号到发送按钮状态更新函数
        self.input_text.input_state_changed.connect(self.update_send_button_state)
        
        input_layout.addWidget(self.input_text)

        # 右侧按钮区域（垂直布局）
        buttons_layout = QVBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # 操作栏展开按钮
        self.expand_button = QPushButton()
        self.expand_button.setFixedSize(50, 25)
        self.expand_button.setIcon(QIcon("assets/images/icon/operation_expand.svg"))
        self.expand_button.setIconSize(QSize(40, 20))
        expand_button_style_sheet = """
        QPushButton {
            border: 1px solid #E6E6E6;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #E4E4E4;
        }
        QPushButton:pressed {
            background-color: #CDCDCD;
        }
        """
        self.expand_button.setStyleSheet(expand_button_style_sheet)
        self.expand_button.clicked.connect(self.toggle_action_bar)
        buttons_layout.addWidget(self.expand_button)

        # 发送按钮
        self.send_button = QPushButton("发送")
        font = QFont(font_family_name)
        font.setPixelSize(14)
        font.setWeight(QFont.Weight.Normal)
        self.send_button.setFont(font)
        self.send_button.setFixedSize(50, 70)
        send_button_style_sheet = """
QPushButton {
    border: none;
    border-radius: 4px;
    background-color: #07C160;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #06B75B;
}
QPushButton:pressed {
    background-color: #06AE56;
}
QPushButton:disabled {
    background-color: #E1E1E1;
    color: #9D9D9D;
}
"""
        self.send_button.setStyleSheet(send_button_style_sheet)
        self.send_button.clicked.connect(self.send_message)
        short_cut = QShortcut(Qt.CTRL | Qt.Key_Return, self.input_text)
        short_cut.activated.connect(self.send_message)
        buttons_layout.addWidget(self.send_button)
        
        input_layout.addLayout(buttons_layout)

        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

        self.thread = QThread()
        self.agent_worker = AgentWorker()

        self.agent_worker.moveToThread(self.thread)

        self.agent_worker.get_assistant_message_dict.connect(self.on_get_assistant_message_dict)
        self.agent_worker.get_tool_result.connect(self.on_get_tool_result)
        self.agent_worker.finished.connect(self.on_finished)
        self.agent_worker.get_message_id.connect(self.on_get_message_id)
        self.id_to_index_mapping = {}
        
        # 初始状态下禁用发送按钮（因为输入框为空）
        self.send_button.setEnabled(False)
        self.is_processing = False  # 添加处理状态标志

        self.thread.start()

    def update_send_button_state(self, has_valid_input):
        """更新发送按钮的启用/禁用状态"""
        # 只有当有有效输入且不在处理中时，才启用发送按钮
        self.send_button.setEnabled(has_valid_input and not self.is_processing)

    def on_get_message_id(self, message_uid, message_index):
        self.id_to_index_mapping[message_uid] = message_index
        # print(self.id_to_index_mapping)

    def insert_message(self, message_id, avatar_path, sender, message_content, reasoning, tool_calls):
        message_widget = MessageWidget(message_id, avatar_path, sender, message_content, reasoning, tool_calls)
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
        # 设置处理状态
        self.is_processing = True
        self.send_button.setEnabled(False)

        raw = self.input_text.toPlainText()

        if raw.strip() == "":
            self.is_processing = False
            # 根据当前输入状态更新按钮
            has_valid_input = not self.input_text._has_preedit and self.input_text.toPlainText().strip() != ""
            self.send_button.setEnabled(has_valid_input)
            return

        user_message_id = uuid.uuid4()
        user_message_index = len(self.agent_worker.main_agent.messages)
        self.on_get_message_id(user_message_id, user_message_index)

        self.insert_message(user_message_id, "./assets/images/avatar/user.svg", "用户", raw, None, None)

        self.input_text.clear()

        self.agent_worker.start_work.emit(raw)

    def on_get_assistant_message_dict(self, message_id, message_dict):
        reasoning = message_dict.get("reasoning")
        content = message_dict.get('content')
        tool_calls = message_dict.get('tool_calls')
        # print(message_dict)
        self.insert_message(message_id, "./assets/images/avatar/assistant.svg", self.agent_worker.main_agent.model_name, content, reasoning, tool_calls)

    def on_get_tool_result(self, message_id, tool_name, tool_content):
        self.insert_message(message_id, "./assets/images/avatar/tool.svg", tool_name, tool_content, None, None)

    def on_finished(self):
        # 重置处理状态
        self.is_processing = False
        # 根据当前输入状态更新按钮
        has_valid_input = not self.input_text._has_preedit and self.input_text.toPlainText().strip() != ""
        self.send_button.setEnabled(has_valid_input)

    def toggle_action_bar(self):
        """切换操作按钮栏的显示/隐藏状态"""
        if self.is_action_bar_expanded:
            self.action_bar.hide()
            self.is_action_bar_expanded = False
        else:
            self.action_bar.show()
            self.is_action_bar_expanded = True

    def clear_messages(self):
        """清空所有消息（保留系统消息）"""
        # 清空UI中的消息控件
        while self.messages_layout.count() > 1:  # 保留最后的stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 清空Agent的消息列表（保留系统消息）
        system_messages = [msg for msg in self.agent_worker.main_agent.messages if msg.get("role") == "system"]
        self.agent_worker.main_agent.messages = system_messages
        
        # 清空ID到索引的映射
        self.id_to_index_mapping.clear()

    def closeEvent(self, event):
        self.thread.quit()
        self.thread.wait()
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        load_font()

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