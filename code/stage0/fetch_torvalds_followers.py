"""从github公开API获取torvalds的followers数量"""
import json
import urllib.request


def main():
    # GitHub REST API: 获取用户 torvalds 的公开信息
    url = "https://api.github.com/users/torvalds"

    # 发送 GET 请求，GitHub API 对公开信息无需认证
    # urlopen(url) 返回一个 HTTPResponse 对象
    with urllib.request.urlopen(url) as response:
        # 读取响应 body（bytes），解码为字符串，再解析为 Python 字典
        data = json.loads(response.read().decode("utf-8"))

    # 从返回的 JSON 中取出 followers 字段并打印
    print(data["followers"])


if __name__ == "__main__":
    main()
