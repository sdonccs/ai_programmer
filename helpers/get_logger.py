import logging

import colorlog


class InfoTruncatingFilter(logging.Filter):
    def __init__(self, name = "", max_length = 3000, placeholder = "...[TRUNCATED]..."):
        super().__init__(name)
        self.max_length = max_length
        self.placeholder = placeholder

    def filter(self, record):
        # 仅对 INFO 级别的日志进行处理
        if record.levelno == logging.INFO:
            # 获取已经格式化了参数的消息字符串
            original_message = record.getMessage()
            if len(original_message) > self.max_length:
                # 截断消息
                half = int(self.max_length / 2)
                truncated_message = original_message[:half] + self.placeholder + original_message[-half:]
                # 用截断后的消息替换原始消息
                record.msg = truncated_message
                record.args = ()
        # 返回 True，确保所有日志记录（无论是否被修改）都能继续被处理
        return True


def get_logger(logger_name: str, max_length: int = 3000):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    truncating_filter = InfoTruncatingFilter(max_length=max_length)
    logger.addFilter(truncating_filter)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    )
    logger.addHandler(handler)

    return logger