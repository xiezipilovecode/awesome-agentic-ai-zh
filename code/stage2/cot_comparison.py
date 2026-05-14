"""
比较三种提示策略对数学推理题的效果
  A: 纯 prompt — 要求直接给答案，禁止解释
  B: Zero-Shot CoT — 加 "Let's think step by step"
  C: Few-Shot CoT — 先展示一个带推理步骤的示例

题目来自 Prompt Engineering Guide：
  "这组数中的奇数加起来是否得到一个偶数?"
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

# 需要多步推理的数学题 — 来自 promptingguide.ai
QUESTION = "下面这组数中的奇数加起来是否得到一个偶数？15、32、5、13、82、7、1。回答是或否。"
CORRECT = "否 (15+5+13+7+1 = 41，是奇数)"

# 一个展示完整 CoT 推理步骤的示例（不同数据）
COT_EXAMPLE = """问题: 下面这组数中的奇数加起来是否得到一个偶数？4、8、9、15、12、2、1。
推理步骤:
1. 先找出所有奇数: 9、15、1
2. 把它们相加: 9 + 15 + 1 = 25
3. 25 是奇数，不是偶数
答案: 否

问题: 下面这组数中的奇数加起来是否得到一个偶数？17、10、19、4、8、12、24。
推理步骤:
1. 先找出所有奇数: 17、19
2. 把它们相加: 17 + 19 = 36
3. 36 是偶数
答案: 是"""

# A: 禁止推理，只要最终答案
PROMPT_A = f'{QUESTION}\n请只回答"是"或"否"，不要解释，不要写任何计算过程。'
# B: Zero-Shot CoT
PROMPT_B = f"{QUESTION}\n\n让我们一步一步地思考。"
# C: Few-Shot CoT
PROMPT_C = f"{COT_EXAMPLE}\n\n问题: {QUESTION}\n推理步骤:"


def ask(label, prompt):
    print(f"\n{'─' * 50}")
    print(f"策略 {label}")
    print(f"{'─' * 50}")
    print(f"Prompt: {prompt[:200].strip()}")
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=300,
    )
    answer = resp.choices[0].message.content
    print(f"\n回复: {answer}")
    print(f"Tokens: {resp.usage.total_tokens} (p={resp.usage.prompt_tokens} c={resp.usage.completion_tokens})")
    return answer


def main():
    print(f"模型: {MODEL}")
    print(f"题目: {QUESTION}")
    print(f"正确答案: {CORRECT}")

    results = {}
    results["A-纯Prompt(禁止推理)"] = ask("A - 纯 Prompt（禁止推理）", PROMPT_A)
    results["B-Zero-Shot CoT"] = ask("B - Zero-Shot CoT", PROMPT_B)
    results["C-Few-Shot CoT"] = ask("C - Few-Shot CoT", PROMPT_C)

    print(f"\n{'=' * 50}")
    print(f"总结: 正确答案 = {CORRECT}")
    print("=" * 50)
    for k, v in results.items():
        summary = v.strip().replace("\n", " ")[:120]
        print(f"  {k}: {summary}")


if __name__ == "__main__":
    main()
