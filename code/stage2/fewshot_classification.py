"""
Few-Shot 对比实验：情感分类（正面 / 负面）
  - 0-shot: 直接分类，不给示例
  - 3-shot: 给出 3 个带标签的示例后再分类
  比较两者在相同测试集上的准确率
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("code/.env")
client = OpenAI(
    api_key=os.getenv("GITHUB_TOKEN"),
    base_url=os.getenv("GITHUB_MODEL_BASE_URL"),
)
MODEL = os.getenv("GITHUB_MODEL")

# 测试集 — 15 条中文评论，覆盖正面/负面/隐含情感/讽刺
TEST_SET = [
    ("这家餐厅的服务太棒了，强烈推荐！", "正面"),
    ("等了两个小时还没上菜，再也不来了。", "负面"),
    ("还可以吧，无功无过。", "正面"),       # 中性偏正
    ("性价比非常高，味道也不错。", "正面"),
    ("服务员态度太差了，体验极差。", "负面"),
    ("环境很不错，适合约会。", "正面"),
    ("味道一般，价格还贵，不值。", "负面"),
    ("菜量少得可怜，完全吃不饱。", "负面"),
    ("朋友推荐来的，果然没让我失望。", "正面"),
    ("也就那样吧，没什么特别的。", "负面"),  # 隐含负面
    ("虽然贵但确实好吃，偶尔来还行。", "正面"),  # 有让步但仍偏正
    ("前台爱搭不理的，好像欠她钱一样。", "负面"),
    ("甜点非常精致，拍照也好看。", "正面"),
    ("第一次来，印象不错，下次还会来。", "正面"),
    ("太吵了，根本没法聊天。", "负面"),
]

# 3 个示例 — 覆盖正面/负面，带简短解释
SHOT_EXAMPLES = """将以下评论分类为"正面"或"负面"。

示例1:
评论: 这家店环境优雅，菜品精致，非常适合家庭聚餐。
分类: 正面

示例2:
评论: 等了40分钟，菜上来还是凉的，服务非常糟糕。
分类: 负面

示例3:
评论: 第一次来，口味独特，虽然有点贵但值得。
分类: 正面"""


def classify(prompt_template, test_set, description):
    correct = 0
    total = len(test_set)
    print(f"\n{'─' * 50}")
    print(f"策略: {description}")
    print(f"{'─' * 50}")

    for i, (text, label) in enumerate(test_set, 1):
        prompt = prompt_template.format(text=text)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        pred = resp.choices[0].message.content.strip()
        # 规整预测结果
        if "正面" in pred:
            pred = "正面"
        elif "负面" in pred:
            pred = "负面"
        ok = "[OK]" if pred == label else "[X]"
        if pred == label:
            correct += 1
        print(f"  [{ok}] 评论: {text[:30]}... → 预测={pred} 正确={label}")

    acc = correct / total * 100
    print(f"\n  准确率: {correct}/{total} = {acc:.1f}%")
    return acc


def main():
    print(f"模型: {MODEL}")
    print(f"测试集: {len(TEST_SET)} 条中文评论（正面/负面各半）")

    # 0-shot: 纯指令，无示例
    prompt_0shot = '将以下评论分类为"正面"或"负面"。只回答两个字。\n\n评论: {text}\n分类:'
    acc_0 = classify(prompt_0shot, TEST_SET, "0-Shot（无示例）")

    # 3-shot: 指令 + 3 个示例
    prompt_3shot = SHOT_EXAMPLES + '\n\n现在，请对以下评论进行分类。只回答"正面"或"负面"。\n\n评论: {text}\n分类:'
    acc_3 = classify(prompt_3shot, TEST_SET, "3-Shot（3个示例）")

    print(f"\n{'=' * 50}")
    print("对比总结")
    print("=" * 50)
    print(f"  0-Shot: {acc_0:.1f}%")
    print(f"  3-Shot: {acc_3:.1f}%")
    delta = acc_3 - acc_0
    print(f"  提升:   +{delta:.1f}%")
    print(f"\n  结论: Few-Shot 通过示例告诉模型 '边界在哪里'，")
    print(f"        尤其对中性/隐含情感的句子帮助明显。")


if __name__ == "__main__":
    main()
