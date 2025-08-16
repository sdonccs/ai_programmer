import os

from openai import OpenAI


siliconflow_client: OpenAI = OpenAI(
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv("SILICONFLOW_API_KEY"),
)
siliconflow_model_names = {
    "deepseek-ai": ["deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1"],
    "moonshotai": ["moonshotai/Kimi-K2-Instruct"],
    "MiniMaxAI": ["MiniMaxAI/MiniMax-M1-80k"]
}


openrouter_client: OpenAI = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
openrouter_model_names = {
    "google": ["google/gemini-2.5-pro-preview"],
    "anthropic": ["anthropic/claude-sonnet-4", "anthropic/claude-opus-4"],
    "x-ai": ["x-ai/grok-4"]
}