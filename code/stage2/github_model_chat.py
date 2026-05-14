from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv("code/.env")

# GitHub Models Marketplace — 用 GitHub PAT 调用 gpt-4o-mini
client = OpenAI(
    api_key=os.getenv("GITHUB_TOKEN"),
    base_url=os.getenv("GITHUB_MODEL_BASE_URL"),
)

MODEL = os.getenv("GITHUB_MODEL")  # gpt-4o-mini

# ============================================================
# 在此修改提示词
# ============================================================
SYSTEM_PROMPT = "You are a helpful assistant."
USER_PROMPT = """/*
Ask the user for their name and say "Hello"
*/"""
TEMPERATURE = 0.7
MAX_TOKENS = 200
# ============================================================


def main():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    reply = response.choices[0].message.content
    print(f"模型: {response.model}")
    print(f"Token: prompt={response.usage.prompt_tokens}, "
          f"completion={response.usage.completion_tokens}, "
          f"total={response.usage.total_tokens}")
    print(f"回复: {reply}")


if __name__ == "__main__":
    main()
