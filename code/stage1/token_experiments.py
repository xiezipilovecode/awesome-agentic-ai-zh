from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv("code/.env")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

SYSTEM_PROMPT = "You are a helpful assistant."


def call(prompt, max_tokens, temperature):
    """封装一次 API 调用，返回 (reply, usage)"""
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content, resp.usage


def experiment_1():
    """max_tokens=1：回复被截断为仅 1 个 token"""
    print("=" * 50)
    print("实验 1: max_tokens=1")
    print("=" * 50)
    reply, usage = call("用一句话介绍什么是机器学习。", max_tokens=1, temperature=0.7)
    # 注意：中文一个 token 通常是不完整的一个字或半个字
    # 英文一个 token 大约是一个短词或子词，因此截断效果完全不同
    print(f"回复: {reply}")
    print(f"Token 用量: prompt={usage.prompt_tokens}, "
          f"completion={usage.completion_tokens}, total={usage.total_tokens}")
    # max_tokens=1 时，模型只能生成 1 个 token 就停止，回复往往不完整
    print("说明: 模型只生成 1 个 token 就被迫停止，回复可能是一个不完整的字或词。\n")


def experiment_2():
    """temperature=0：输出确定性最强，每次结果一致"""
    print("=" * 50)
    print("实验 2: temperature=0（确定性输出）")
    print("=" * 50)
    prompt = "用一句话介绍什么是机器学习。"

    # 调用 3 次，观察温度对输出的影响：temperature=0 时每次结果相同
    for i in range(3):
        reply, usage = call(prompt, max_tokens=100, temperature=0)
        print(f"第 {i+1} 次: {reply}")
    print("说明: temperature=0 时，模型每次选择概率最高的 token，输出完全确定。\n")


def experiment_3():
    """比较中文 vs 英文的 token 数量"""
    print("=" * 50)
    print("实验 3: 中文 vs 英文 token 数量对比")
    print("=" * 50)

    # 三组对比：中文与英文含义相近的句子
    pairs = [
        ("你好世界",   "Hello World"),
        ("机器学习是人工智能的一个分支，它通过数据学习模式和规律。",
         "Machine learning is a branch of artificial intelligence that learns patterns from data."),
        ("猫坐在垫子上。", "The cat sat on the mat."),
    ]

    for cn, en in pairs:
        # 只统计 prompt tokens（用户消息），不实际生成回复
        usage_cn = _count_tokens(cn)
        usage_en = _count_tokens(en)
        # 打印结果，包括 token 数量和字符数
        print(f"中文: \"{cn}\"")
        print(f"  → 字符数={len(cn)}, token 数={usage_cn.prompt_tokens}")
        print(f"英文: \"{en}\"")
        print(f"  → 字符数={len(en)}, token 数={usage_en.prompt_tokens}")
        print(f"  中文 token / 英文 token = {usage_cn.prompt_tokens / usage_en.prompt_tokens:.2f}")
        print()
    print("说明: 中文字符 token 效率差异明显：相同含义，中文通常用更少 token。\n")


def _count_tokens(text):
    """用一条简单消息让 API 告诉我们 prompt 占用了多少 token"""
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text},
        ],
        max_tokens=1,
        temperature=0,
    )
    return resp.usage


def main():
    experiment_1()
    experiment_2()
    experiment_3()


if __name__ == "__main__":
    main()
