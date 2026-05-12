import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载 code/.env 中的环境变量（含 DEEPSEEK_API_KEY）
load_dotenv("code/.env")

# 创建 OpenAI 兼容客户端，指向 DeepSeek 的 API 地址
# DeepSeek 的 API 与 OpenAI SDK 完全兼容，只需替换 base_url
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


def main():
    # 调用 Chat Completions API，向模型发送一条消息
    response = client.chat.completions.create(
        model="deepseek-chat",          # DeepSeek-V3 对话模型
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "用一句话介绍什么是机器学习。"},
        ],
        max_tokens=200,  # 限制回复的最大 token 数
        temperature=0.7,  # 控制回复的创造性，0.7 是一个常用的值，数值越高回复越多样化，数值越低回复越保守
    )

    # 提取助手的回复文本
    reply = response.choices[0].message.content

    # 打印 token 用量和回复内容
    print(f"模型: {response.model}")
    print(f"Token 用量: prompt={response.usage.prompt_tokens}, "  # prompt_tokens 是用户消息和系统消息所使用的 token 数
          f"completion={response.usage.completion_tokens}, "  # completion_tokens 是模型生成的回复所使用的 token 数
          f"total={response.usage.total_tokens}")  # total_tokens 是 prompt_tokens 和 completion_tokens 的总和
    print(f"回复: {reply}")


if __name__ == "__main__":
    main()
