import os

from openai import OpenAI


openrouter_client: OpenAI = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

openrouter_model_names = {
    "google": [
        "google/gemini-2.5-pro-preview",  # {首选}[思考]综合能力第一（价格中）（工具调用能力强）
    ],
    "anthropic": [
        "anthropic/claude-sonnet-4",  # {首选}[思考]编程能力第二（价格中）（工具调用能力强）
        "anthropic/claude-opus-4"  # [思考]编程能力第一（价格高）（工具调用能力强）
    ],
    "qwen": [
        "qwen/qwen3-coder"  # 编程能力第三（价格低）（工具调用能力弱）
    ],
    "moonshotai": [
        "moonshotai/kimi-k2"  # 综合能力第二（价格低）（工具调用能力中）
    ]
}