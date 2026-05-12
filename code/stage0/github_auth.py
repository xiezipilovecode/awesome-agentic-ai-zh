"""解释一下REST API
REST API（Representational State Transfer Application Programming Interface）是一种基于HTTP协议的设计风格，用于构建网络应用程序。REST API通过定义资源（如用户、文章等）和使用HTTP方法（如GET、POST、PUT、DELETE）来操作这些资源，使得客户端和服务器之间能够进行通信。
在这个代码示例中，我们使用了GitHub的REST API来获取当前用户的信息。我们定义了一个函数`call_api`，它接受一个可选的Bearer token参数，并使用`urllib.request`库发送HTTP请求到GitHub的`/user`端点。
- 如果没有提供token，GitHub会返回401 Unauthorized错误，因为这个端点需要认证。
- 如果提供了有效的token，GitHub会返回200 OK状态码，并且响应体中包含当前用户的信息（如用户名、ID等）。
通过这个示例，我们可以看到REST API的基本使用方式，以及如何通过HTTP请求来访问受保护的资源。
"""

import os
import urllib.request  # 用于发送 HTTP 请求
import json

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv("code/.env")

TOKEN = os.getenv("GITHUB_TOKEN")
URL = "https://api.github.com/user"


def call_api(token=None):
    """用可选的 Bearer token 调用 GitHub /user endpoint，返回 (status, body)"""
    req = urllib.request.Request(URL)

    if token:
        # 在请求头中加入 Authorization，格式为 "Bearer <token>"
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req) as resp:  # 发送请求并获取响应
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # HTTP 错误（如 401）会被 urlopen 抛出，在这里捕获并返回状态码和错误信息
        return e.code, json.loads(e.read().decode("utf-8"))


def main():
    # 1. 不带 token 请求 → 预期 401 Unauthorized
    print("=== 无 Token（预期 401）===")
    status, body = call_api(token=None)
    print(f"HTTP Status: {status}")
    print(f"Response:    {json.dumps(body, indent=2, ensure_ascii=False)}")

    print()

    # 2. 带 token 请求 → 预期 200，返回当前用户信息
    print("=== 带 Token（预期 200）===")
    status, body = call_api(token=TOKEN)
    print(f"HTTP Status: {status}")
    print(f"Response:    {json.dumps(body, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
