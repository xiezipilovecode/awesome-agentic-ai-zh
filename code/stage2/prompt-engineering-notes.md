# OpenAI Prompt Engineering 学习笔记

> 来源: [OpenAI Prompt Engineering Guide](https://developers.openai.com/api/docs/guides/prompt-engineering)
> 学习日期: 2026-05-13

---

## 1. 两大基本原则

| 原则 | 说明 |
|------|------|
| **写清晰具体的指令** | 长而明确的 prompt 好过短而模糊的，**清晰 > 简短** |
| **给模型时间"思考"** | 对复杂任务要求逐步推理（Chain-of-Thought），不要让它直接给答案 |

---

## 2. 七大核心策略

### 2.1 用分隔符标记输入区域

分隔符（三重引号 ` ``` `、XML 标签等）防止 prompt injection，明确边界：

```python
prompt = f"""
将用三重反引号包裹的文本总结为一句话。
```{user_text}```
"""
```

**作用**: 把"指令"和"数据"清晰分开，模型不会把用户输入误解为指令。

### 2.2 要求结构化输出（JSON）

需要程序化解析时，明确要求 JSON：

```python
prompt = """
生成 3 本书的信息（书名、作者、类型），用 JSON 格式输出。
键名: book_id, title, author, genre
"""
```

**进阶**: GPT-4o+ 可使用 `response_format={"type": "json_schema", "schema": {...}}` 强制 JSON 输出。

### 2.3 先验条件检查

让模型在执行前验证前提条件：

```python
prompt = f"""
如果文本中包含步骤指令，按「步骤1 - ...」格式重写。
如果没有指令，回复"无步骤"。
文本: {text}
"""
```

### 2.4 Few-Shot Prompting（少样本提示）

提供 1-2 个示例来规范输出格式和风格：

```python
prompt = """
用一致的风格回答：

<孩子>: 教我什么是耐心。
<老人>: 雕刻最深峡谷的河流，源于最温和的泉源...

<孩子>: 教我什么是韧性。
"""
```

**关键**: 示例比描述更有效，模型从例子中学到的比从规则中学到的多。

### 2.5 分步拆解复杂任务

将复杂任务分解为有序子任务：

```python
prompt = f"""
依次执行：
1. 用 1 句话总结文本
2. 将总结翻译为法语
3. 列出法语总结中所有名字
4. 输出 JSON: {{"french_summary": ..., "num_names": ...}}

文本: <{text}>
"""
```

### 2.6 自我解答后再对比（防"偷看"）

做评判任务时，要求模型先自己求解再对比：

```python
prompt = """
先独立计算你的答案，再对比学生的答案。
只有在这之后，才判断学生是否正确。
"""
```

**原因**: 如果先看到学生答案，模型容易受其影响而产生推理偏差。

### 2.7 基于源材料回答（防幻觉）

提供权威源文本并要求引用：

```python
prompt = f"""
仅基于以下源文本回答。如果信息不存在，回答"未知"，不要猜测。

源文本: {source_text}
问题: {question}
"""
```

---

## 3. GPT-5 / GPT-4.1 现代 Prompt 模式（2025-2026）

### 3.1 "结果导向"范式

新模型更倾向于**结果导向的 prompt** 而非冗长的逐步指令：

| ❌ 旧风格 | ✅ 新风格 |
|-----------|-----------|
| "先读政策，再检查账户，然后对比字段，再决定..." | "端到端解决客户问题。成功标准：资格判断仅使用可用的政策和账户数据。最终输出包含：已完成动作、客户消息、阻塞项。" |

### 3.2 角色 + 目标 + 护栏模式

```python
system_prompt = """
# Personality（角色）
你是一个有能力的协作者：平易近人、冷静、直接。
假设用户是能干的。保持简洁但有礼貌。

# Goal（目标）
为搜索重新设计功能起草一页 PRD。

# Guardrails（护栏）
- 最多 5 个章节（问题、用户、需求、风险、指标）
- 每章 ≤ 150 词
- 写作前先问 3 个澄清问题
- 使用简洁的非营销语言
"""
```

### 3.3 新 API 参数

```python
response = client.chat.completions.create(
    model="gpt-5.5",
    messages=[...],
    reasoning_effort="low",   # none | low | medium | high | xhigh
    temperature=0.7,
    max_tokens=500,
)
```

| 参数 | 用途 |
|------|------|
| `reasoning_effort` | 控制推理深度（越低越快越便宜） |
| `text.verbosity` | `low` 精简输出，`medium` 平衡 |
| `temperature` | `0-0.2` 确定性任务；`0.7-1.0` 创意任务 |
| `response_format` | `{"type": "json_schema", ...}` 保证结构化输出 |

---

## 4. 迭代开发流程

最重要的元技能 —— 没有一个 prompt 第一次就完美：

```
想法 → 写 Prompt → 运行 → 分析输出 → 改进 Prompt → 循环
```

| 迭代 | 发现的问题 | 修复 |
|------|-----------|------|
| 1 | 输出太长 | 加字数/句数限制 |
| 2 | 焦点/受众不对 | 指定受众和侧重点 |
| 3 | 缺少关键字段 | 要求提取特定数据 |
| 4 | 格式不可解析 | 要求结构化输出 (JSON/HTML) |
| 5 | 需要可视化 | 添加 HTML 渲染指令 |

**黄金法则**: 每次迭代只改**一个变量**，精确判断效果来源。

---

## 5. 多 Agent 自动优化 Prompt（OpenAI Cookbook 2025.7）

用专用 Agent 并行审查 Prompt 质量：

```python
# 三个 checker 并行执行
contradiction_checker = Agent(  # 检测自相矛盾
    name="contradiction_detector",
    instructions="Detect self-contradictions..."
)
format_checker = Agent(  # 检查输出格式
    name="format_checker",
    instructions="Flag missing format specs..."
)
fewshot_checker = Agent(  # 检查示例一致性
    name="fewshot_consistency_checker",
    instructions="Find conflicts between rules and examples..."
)
```

流程: **多个 Checker 并行 → Rewriter 修复 → 输出优化后的 Prompt**

---

## 6. 生产级 API 调用封装

```python
from openai import OpenAI

def get_completion(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4.1",
    temperature: float = 0.0,
) -> str:
    """统一的 chat completions 调用封装"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content
```

---

## 7. 核心要点总结

1. **显式胜于隐式** — GPT-5 会忠实地执行你字面上的意思（包括错误），务必精确
2. **迭代，不要执念第一次就完美** — 把 prompt 当原型对待，快速改版
3. **结构化输出是你的朋友** — 尽可能使用 `response_format` + JSON Schema
4. **角色 + 目标 + 护栏** — 现代 system prompt 的三位一体
5. **基于源材料** — 粘贴权威文本，要求引用，以对抗幻觉
6. **自我检查** — 要求模型对照 checklist 批判自己的输出
7. **`temperature=0` 用于确定性任务** — 代码、数学、信息提取、事实问答

---

## 8. 提示技术详解

> 来源: [Prompt Engineering Guide - 提示技术](https://www.promptingguide.ai/zh/techniques)
> 学习日期: 2026-05-14

### 8.1 技术全景图

```
基础 ──→ 进阶 ──→ 高级 ──→ Agent 级

Zero-Shot  →  Few-Shot  →  CoT  →  Self-Consistency  →  ToT
                                ↘                      ↘
                              Generate Knowledge      ReAct → Reflexion
                                ↘
                              PAL / ART / APE
```

共收录 **17 种**提示技术，分四个层级逐步递进。

---

### 8.2 基础级技术

#### Zero-Shot（零样本提示）

**直接提问，不提供任何示例。**

```
将以下文本分类为中性、负面或正面。
文本：我认为这次假期还可以。
情感：
```

现代 LLM 通过**指令微调 + RLHF** 具备了零样本能力。当零样本不工作时，升级为少样本。

#### Few-Shot（少样本提示）

**在 prompt 中嵌入 1~N 个示例（1-shot / few-shot），让模型从示例中学习输出格式。**

核心发现（Min et al. 2023）：
- **格式比标签正确性更重要** — 即使随机打乱标签，只要格式一致就有效果
- 示例从**真实标签分布**中采样优于均匀采样
- 大模型对格式不一致也表现出更强的鲁棒性

**局限**：对算术推理等需要多步逻辑的任务仍然失败，需升级到 CoT。

---

### 8.3 推理级技术

#### Chain-of-Thought / CoT（思维链提示）

**核心：在 prompt 中展示中间推理步骤，引导模型"边想边说"。**

**Few-Shot CoT**（Wei et al. 2022）：
```
Q: 这组数中奇数之和是否为偶数？15, 32, 5, 13, 82, 7, 1
A: 奇数有 15, 5, 13, 7, 1。15+5=20, 20+13=33, 33+7=40, 40+1=41。答案为 False。
```
只需 1 个带推理步骤的示例即可显著提升算术推理正确率。

**Zero-Shot CoT**（Kojima et al. 2022）：
加一句 **"让我们逐步思考"** 即可，零示例触发推理链。
```
我去市场买了10个苹果...让我们逐步思考。
→ 从10个苹果开始 → 给邻居2个剩8个 → 给修理工2个剩6个 → 买5个有11个 → 吃1个剩10个。答案：10。
```

**Auto-CoT**（Zhang et al. 2022）：自动聚类问题 → 采样代表性问题 → 用 Zero-Shot-CoT 生成推理链，消除手工设计示例的劳动。用问题长度和推理步数作为启发式选择简单准确的演示。

#### PAL（程序辅助语言模型）

**将推理步骤卸载给 Python 解释器执行，而非用自然语言描述数学计算。**

```
Q: 今天是 2023年2月27日，我正好25年前出生。出生日期是？
→ today = datetime(2023, 2, 27)
→ born = today - relativedelta(years=25)
→ born.strftime("%m/%d/%Y")  # 02/27/1998
```

与 CoT 的关键区别：计算由**代码执行**而非 LLM 文本生成，消除算术错误。

#### Self-Consistency（自一致性）

**对同一问题用 CoT 采样多条推理路径，取出现次数最多的答案作为最终结果。**

（Wang et al. 2022）本质是"用投票替代贪心解码"：temperature > 0 → 多次采样 → 多数表决。配合 CoT 使用效果最佳，代价是 token 成本翻倍。

---

### 8.4 外部知识级技术

#### Generate Knowledge（生成知识提示）

**两步法**（Liu et al. 2021）：
1. 先让 LLM 围绕问题**生成背景知识**
2. 将知识拼入 prompt，再让 LLM **基于知识推理**

```
步骤1: 输入"高尔夫球的目标？"
       知识: 用最少杆数将球打入洞中，总杆数最低者获胜。

步骤2: 问题 + 知识 → 推理
       答案: 不是比得分更高，是比谁用最少杆数完成。
```

**适用**: 常识推理等需要外部知识但仍依赖 LLM 内部知识的场景。

#### RAG（检索增强生成）

**将信息检索组件和文本生成模型结合**（Lewis et al. 2021）。

工作流程：输入 → 检索相关支撑文档（如维基百科） → 文档作为上下文 + 原始 prompt → 文本生成器输出。LLM 参数化知识是静态的，RAG 让模型**无需重新训练就能获取最新信息**。MS-MARCO、Jeopardy、FEVER 等基准测试中 RAG 生成的答案更符合事实、更具体。

#### ReAct（推理 + 行动框架）

**将 LLM 的推理能力和外部工具调用组合**（Yao et al. 2022），循环执行：**思考 → 行动 → 观察 → 思考 → ...**

```
思考: 需要搜索科罗拉多造山带东部区域
行动: 搜索[科罗拉多造山带] → 观察: 东部延伸到高平原
思考: 需要搜索高平原海拔
行动: 搜索[高平原] → 观察: 海拔 1800-7000 英尺
思考: 答案 = 1800-7000 英尺
```

| | CoT | ReAct |
|------|------|------|
| 内部推理 | ✓ | ✓ |
| 外部工具 | ✗ | ✓ |
| 事实幻觉 | 高 | 低 |
| 推理灵活性 | 高 | 受检索质量约束 |

**最佳实践**：ReAct + CoT + Self-Consistency 三者组合效果最优。LangChain 原生支持 `zero-shot-react-description` agent。

#### Reflexion（自我反思）

**在 ReAct 基础上增加自我评估和自我反思能力**（Shinn et al. 2023），由三个模型组成：
- **Actor**：执行动作，生成轨迹
- **Evaluator**：评价 Actor 输出，给出奖励分数
- **Self-Reflection**：LLM 生成语言反馈存为长期记忆，指导下一次尝试

循环流程：定义任务 → 生成轨迹 → 评估 → **自我反思** → 下一轮生成。

**优势**：
- 不需要微调 LLM，轻量级替代传统强化学习
- 语言反馈比标量奖励更细致具体
- 在 AlfWorld（130/134 任务）、HotPotQA、HumanEval 编程等任务上显著提升

---

### 8.5 高级搜索/规划级技术

#### Tree of Thoughts / ToT（思维树）

**维护一棵"思维树"，每个节点是一个推理中间步骤**（Yao et al. 2023）。

三步循环：
1. **生成**：每步产生多个候选思维
2. **评估**：LLM 自己将思维评估为 sure / maybe / impossible
3. **搜索**：BFS（广度优先）或 DFS，走不通可回溯

以"算 24 点"为例：3 个思维步骤，每步保留 5 个最优候选项，BFS 搜索。ToT 在数学推理任务上的表现远超标准 CoT。

**简化版 ToT Prompt**：
```
假设三位不同的专家来回答这个问题。所有专家写下第一个思考步骤并分享。
然后写下下一步并分享，直到都写完。发现有专家步骤出错了就让其退出。
```

#### ART（自动推理并使用工具）

**自动从任务库中选取多步推理+工具使用示范**（Paranjape et al. 2023），零样本完成新任务。调用外部工具时**自动暂停生成**，整合工具输出后继续。在 BigBench 和 MMLU 基准上超过少样本 CoT，配合人类反馈后超过手写 CoT。

---

### 8.6 提示优化级技术

#### APE（自动提示工程师）

**用 LLM 自动生成和选优提示词**（Zhou et al. 2022）。流程：推理模型接收输出演示 → 生成指令候选项 → 目标模型执行 → 按评估分数选最优。

APE 发现的最优 CoT 触发词：**"让我们一步一步地解决这个问题，以确保我们有正确的答案。"** — 比人工 "Let's think step by step" 效果更好。

#### Active-Prompt

**主动选择最不确定的问题让人类标注**，而非随机选示例。先用 CoT 查询一批问题 → 计算每个答案的**不确定度**（不一致性） → 选出最不确定的让人工标注 → 用新标注示例改进后续推理。

#### DSP（方向性刺激提示）

训练一个**小型策略模型**生成刺激/引导指令，控制冻结的大黑盒 LLM 生成方向。策略模型可以很小且可优化，用于指导黑盒 LLM 完成摘要等任务。

---

### 8.7 视觉/图级别技术

#### Multimodal CoT（多模态思维链）

将传统 CoT 从纯文本拓展到**文本+视觉**。两阶段框架：先基于多模态信息**生成推理依据**，再**推导最终答案**。1B 参数的 Multimodal CoT 在 ScienceQA 上超过 GPT-3.5。

#### GraphPrompts

新型图提示框架（Liu et al. 2023），用于图相关下游任务的性能提升。在提示中嵌入**图结构信息**引导 LLM 推理。

---

### 8.8 技术选择指南

| 任务类型 | 推荐技术 | 备注 |
|---------|---------|------|
| 简单分类/情感分析 | Zero-Shot / Few-Shot | 不行就加示例 |
| 格式精确控制 | Few-Shot（重点在格式） | 格式 > 标签正确性 |
| 数学/算术推理 | PAL 或 CoT | PAL 用代码执行更准确 |
| 复杂多步推理 | CoT + Self-Consistency | 投票提升稳定性 |
| 需要计算日期/数值 | PAL | 用 Python 而非 LLM 算 |
| 常识推理 | Generate Knowledge | 先产知识再推理 |
| 需要最新外部信息 | RAG 或 ReAct | RAG 偏检索，ReAct 偏交互 |
| 搜索 + 推理 + 问答 | ReAct + CoT + Self-Consistency | 三合一最稳健 |
| 策略探索/规划 | ToT | 多路径 + 可回溯 |
| 试错学习 | Reflexion | 从历史错误中自我改进 |
| 自动优化 prompt | APE / Active-Prompt | LLM 替代人工调 prompt |
| 图数据推理 | GraphPrompts | 嵌入图结构到 prompt |
| 图文混合推理 | Multimodal CoT | 文本+视觉联合推理 |
| 零样本新任务 | ART | 自动选示范+工具 |

### 8.9 关键论文速查

| 技术 | 论文 | 年份 |
|------|------|------|
| CoT | Wei et al. "Chain-of-Thought Prompting" | 2022 |
| Zero-Shot CoT | Kojima et al. "Large Language Models are Zero-Shot Reasoners" | 2022 |
| Auto-CoT | Zhang et al. "Automatic Chain of Thought Prompting" | 2022 |
| Self-Consistency | Wang et al. "Self-Consistency Improves Chain of Thought Reasoning" | 2022 |
| PAL | Gao et al. "PAL: Program-aided Language Models" | 2022 |
| Generate Knowledge | Liu et al. "Generated Knowledge Prompting" | 2021 |
| RAG | Lewis et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" | 2021 |
| ReAct | Yao et al. "ReAct: Synergizing Reasoning and Acting in Language Models" | 2022 |
| Reflexion | Shinn et al. "Reflexion: Language Agents with Verbal Reinforcement Learning" | 2023 |
| ToT | Yao et al. "Tree of Thoughts: Deliberate Problem Solving" | 2023 |
| ART | Paranjape et al. "ART: Automatic multi-step reasoning and tool-use" | 2023 |
| APE | Zhou et al. "Large Language Models are Human-Level Prompt Engineers" | 2022 |
| Active-Prompt | Diao et al. "Active Prompting with Chain-of-Thought" | 2023 |
| Multimodal CoT | Zhang et al. "Multimodal Chain-of-Thought Reasoning" | 2023 |
| DSP | Li et al. "Directional Stimulus Prompting" | 2023 |
| GraphPrompts | Liu et al. "GraphPrompt: Unifying Pre-Training and Downstream" | 2023 |