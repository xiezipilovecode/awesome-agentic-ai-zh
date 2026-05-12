import yaml

CONFIG_PATH = "code/stage0/config.yaml"


def main():
    # 1. 读取 YAML 文件，解析为 Python 字典
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)  # safe_load 避免任意代码执行

    print("=== 修改前 ===")
    print(f"debug = {config['app']['debug']}")
    print(f"port  = {config['server']['port']}")

    # 2. 修改字典中的值
    config["app"]["debug"] = False         # 开启调试模式
    config["server"]["port"] = 9090       # 更换端口号

    print("\n=== 修改后 ===")
    print(f"debug = {config['app']['debug']}")
    print(f"port  = {config['server']['port']}")

    # 3. 将修改后的字典写回 YAML 文件
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(
            config, f,
            allow_unicode=True,           # 支持中文
            default_flow_style=False,     # 使用块风格（不是内联 JSON 风格）
            sort_keys=False,              # 保留原有键的顺序
        )

    print("\n已写入 config.yaml")


if __name__ == "__main__":
    main()
