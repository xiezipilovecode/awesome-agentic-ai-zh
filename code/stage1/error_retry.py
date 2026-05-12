import time
import random
from openai import (
    OpenAI,
    AuthenticationError,
    BadRequestError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from dotenv import load_dotenv
import os

load_dotenv("code/.env")

# ============================================================
# 判断：哪些错误值得重试，哪些应该立刻失败
# ============================================================

# 不可重试的错误类型 —— 重试一万次也不会变
FATAL_ERRORS = (
    AuthenticationError,   # API key 错误 / 权限不足  → 直接 raise
    BadRequestError,       # 参数错误 / prompt 超长   → 直接 raise
)

# 可重试的错误类型 —— 网络波动、服务端临时故障
RETRYABLE_ERRORS = (
    APIConnectionError,    # DNS 解析失败、连接被拒绝
    APITimeoutError,       # 请求超时
    InternalServerError,   # 服务端 500（暂时性）
    RateLimitError,        # 被限流，等一等就好
)


def chat_with_retry(client, model, messages, max_tokens=200,
                    temperature=0.7, max_retries=5, base_delay=1.0):
    """
    带 exponential backoff 的 chat completions 调用。

    参数:
        max_retries: 最大重试次数
        base_delay: 基础等待秒数，每次重试延迟翻倍

    逻辑:
        - FATAL_ERRORS → 直接 raise，不重试
        - RETRYABLE_ERRORS → exponential backoff 重试
        - 未知错误 → 同样尝试重试（保守策略）
    """
    for attempt in range(max_retries + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except FATAL_ERRORS as e:
            # API key 错误、prompt 超长等 → 不重试，立刻抛出
            print(f"[致命错误] {type(e).__name__}: {e}")
            raise
        except RETRYABLE_ERRORS as e:
            if attempt == max_retries:
                print(f"[重试耗尽] {type(e).__name__}，已重试 {max_retries} 次")
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[可重试错误] {type(e).__name__}: {e}")
            print(f"  → 第 {attempt + 1}/{max_retries} 次重试，等待 {delay:.1f}s...")
            time.sleep(delay)
        except Exception as e:
            # 未知错误，保守处理：也重试
            if attempt == max_retries:
                print(f"[未知错误，重试耗尽] {type(e).__name__}: {e}")
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"[未知错误] {type(e).__name__}: {e}")
            print(f"  → 第 {attempt + 1}/{max_retries} 次重试，等待 {delay:.1f}s...")
            time.sleep(delay)


def build_normal_client():
    """正常客户端"""
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )


def build_bad_key_client():
    """API key 故意写错"""
    return OpenAI(
        api_key="sk-this-is-a-fake-key-12345",
        base_url="https://api.deepseek.com",
    )


def build_bad_base_url_client():
    """base_url 故意写错 → 模拟网络不可达"""
    return OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.this-does-not-exist-xyz123.com",
    )


# ============================================================
# 三个实验
# ============================================================

def experiment_bad_api_key():
    """场景 1: API key 错误 → FATAL，直接 raise"""
    print("=" * 50)
    print("实验 1: 错误的 API Key（应直接报错，不重试）")
    print("=" * 50)
    client = build_bad_key_client()
    try:
        chat_with_retry(client, "deepseek-chat", [
            {"role": "user", "content": "Hello"},
        ])
    except Exception as e:
        print(f"→ 最终捕获: {type(e).__name__}\n")


def experiment_context_overflow():
    """场景 2: prompt 不合规 → BadRequestError，直接 raise，不重试"""
    print("=" * 50)
    print("实验 2: 参数错误 / Prompt 超限（应直接报错，不重试）")
    print("=" * 50)
    client = build_normal_client()

    # 先演示 token 计数：用 tiktoken 精确估算
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")

    parts = []
    token_count = 0
    while token_count < 200_000:
        chunk = ' '.join(
            ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(3, 10)))
            for _ in range(1000)
        )
        parts.append(chunk)
        token_count += len(enc.encode(chunk))
    huge_text = ' '.join(parts)
    actual_tokens = len(enc.encode(huge_text))
    print(f"生成随机文本: {actual_tokens:,} tokens（远超 128K context window）")
    print(f"  注: DeepSeek 实际会对超长 prompt 做静默截断，不抛异常")

    # 改用另一种方式触发 BadRequestError：传空 messages 列表
    # 这同样是 BadRequestError → FATAL，不重试
    print("\n触发 BadRequestError（空 messages 列表）:")
    try:
        chat_with_retry(client, "deepseek-chat", [])
    except BadRequestError:
        print("→ 最终捕获: BadRequestError（不重试，直接失败）\n")


def experiment_network_error():
    """场景 3: 网络不可达 → 应触发 retry + exponential backoff"""
    print("=" * 50)
    print("实验 3: 网络错误（应触发 exponential backoff 重试）")
    print("=" * 50)
    client = build_bad_base_url_client()
    try:
        chat_with_retry(
            client, "deepseek-chat",
            [{"role": "user", "content": "Hello"}],
            max_retries=3,
            base_delay=1.0,
        )
    except Exception as e:
        print(f"→ 最终捕获: {type(e).__name__}（已重试 3 次后仍失败）\n")


def main():
    experiment_bad_api_key()
    experiment_context_overflow()
    experiment_network_error()

    print("=" * 50)
    print("总结")
    print("=" * 50)
    print("""
错误分类策略:
  ┌─ AuthenticationError / BadRequestError → FATAL，直接 raise
  └─ ConnectionError / Timeout / 5xx       → RETRYABLE，exponential backoff

Retry 参数:
  - max_retries=5, base_delay=1s
  - delay = base_delay * 2^attempt + jitter(0~1s)
  - 实际等待: 1s → 2s → 4s → 8s → 16s
""")


if __name__ == "__main__":
    main()
