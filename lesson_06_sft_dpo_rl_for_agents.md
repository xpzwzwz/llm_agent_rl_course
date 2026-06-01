# 第六课：用 SFT、DPO、PPO 和 GRPO 训练 Agent

## 1. 先看总流程

Agent post-training 不应该一开始就上在线 RL。更稳的顺序是：

```text
收集任务 -> 跑 agent -> 记录 trajectory -> 验证成功/失败
       -> SFT 学格式和基本策略
       -> DPO 学偏好和避免坏策略
       -> GRPO/PPO 在可验证环境里继续优化
       -> 固定 benchmark 回归评估
```

这条路线背后的原因很简单：

- SFT 解决“模型会不会按你的 agent 协议行动”。
- DPO 解决“模型能不能偏好更好的轨迹”。
- GRPO/PPO 解决“模型能不能在环境反馈里探索出更高成功率策略”。

如果没有稳定工具协议和评估器，直接 RL 通常只会放大奖励漏洞。

## 2. 数据统一格式

不管后面做 SFT、DPO 还是 RL，原始数据都建议先统一成 trajectory：

```json
{
  "task_id": "github_fix_0001",
  "task": "修复 parser 空输入导致的测试失败。",
  "environment": "docker://parser_repo_v1",
  "tools": ["read_file", "search_repo", "edit_file", "run_tests"],
  "trajectory": [
    {
      "observation": "pytest 显示 test_empty_input 失败。",
      "action": {
        "name": "read_file",
        "arguments": {"path": "src/parser.py"}
      },
      "result": "parse() 没有处理空字符串。"
    },
    {
      "action": {
        "name": "edit_file",
        "arguments": {"path": "src/parser.py", "patch": "..."}
      },
      "result": "编辑成功。"
    },
    {
      "action": {
        "name": "run_tests",
        "arguments": {"command": "pytest tests/test_parser.py -q"}
      },
      "result": "4 passed"
    }
  ],
  "final": "已修复空输入处理，相关测试通过。",
  "final_status": "success",
  "final_reward": 1.0
}
```

这份原始轨迹可以转换成不同训练格式：

- SFT：`prompt -> completion` 或 `messages`。
- DPO：`prompt -> chosen/rejected`。
- GRPO/PPO：`prompt + environment + reward function`。

## 3. SFT：让模型先会走路

SFT 是监督微调。TRL 官方文档里，SFTTrainer 支持 language modeling、prompt-completion 和 conversational dataset；对 agent 来说，最常用的是 conversational 格式，并且只在 assistant 输出上算 loss。

Agent SFT 的目标：

- 输出合法工具调用。
- 遵守 JSON/schema。
- 根据 observation 继续行动。
- 在最终回答之前做必要验证。
- 学会失败恢复轨迹。

一个 SFT 样本可以写成：

```json
{
  "messages": [
    {
      "role": "system",
      "content": "你是代码修复 agent。可用工具：read_file, search_repo, edit_file, run_tests。"
    },
    {
      "role": "user",
      "content": "修复 parser 空输入导致的测试失败。"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "run_tests",
            "arguments": "{\"command\":\"pytest tests/test_parser.py -q\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_1",
      "content": "FAILED test_empty_input: ValueError"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_2",
          "type": "function",
          "function": {
            "name": "read_file",
            "arguments": "{\"path\":\"src/parser.py\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_2",
      "content": "def parse(text): return text.split(',')"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_3",
          "type": "function",
          "function": {
            "name": "edit_file",
            "arguments": "{\"path\":\"src/parser.py\",\"patch\":\"if not text: return []\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_3",
      "content": "edited"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_4",
          "type": "function",
          "function": {
            "name": "run_tests",
            "arguments": "{\"command\":\"pytest tests/test_parser.py -q\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_4",
      "content": "4 passed"
    },
    {
      "role": "assistant",
      "content": "已修复空输入处理，测试通过。"
    }
  ]
}
```

训练时要注意：

- 只把高质量成功轨迹、或失败后成功恢复的轨迹放进 SFT。
- 不要让模型学习工具返回值，loss 应该主要落在 assistant tool call 和最终回答上。
- 保持工具名、参数名和返回格式稳定。
- 长轨迹要截断或分段，否则模型学到很多噪声。
- 混入一部分普通聊天/推理数据，避免 agent 化后通用能力下降。

SFT 常见失败：

- 模型只会输出自然语言，不会调用工具：工具调用样本太少或格式不一致。
- 模型会调用工具但参数乱填：schema 太宽，缺少参数错误样本。
- 模型过早 final：训练集中缺少“先验证再结束”的示范。
- 模型机械重复步骤：轨迹里重复无效动作没有清洗。

## 4. DPO：让模型偏好好轨迹

DPO 不需要显式训练 reward model。TRL 的 DPOTrainer 要求 preference dataset，典型格式是：

```json
{
  "prompt": "The sky is",
  "chosen": " blue.",
  "rejected": " green."
}
```

Agent 里要比较的是整条轨迹：

```json
{
  "prompt": "修复 parser 空输入导致的测试失败。",
  "chosen": [
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "run_tests", "arguments": "{\"command\":\"pytest -q\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "FAILED"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\":\"src/parser.py\"}"}}]},
    {"role": "tool", "tool_call_id": "call_2", "content": "def parse(text): ..."},
    {"role": "assistant", "content": "已修复，测试通过。"}
  ],
  "rejected": [
    {"role": "assistant", "content": "可能是 parse 函数没有处理空输入，但我还没有验证。"}
  ]
}
```

chosen/rejected 的来源：

- 同一任务多次采样，成功轨迹作为 chosen，失败轨迹作为 rejected。
- 人工标注两条轨迹，选择更稳的一条。
- 自动 verifier 判定：测试通过优于测试失败。
- 规则判定：运行验证优于未验证，少量有效步骤优于大量重复步骤。

Agent DPO 的偏好维度：

- 任务完成优于未完成。
- 有验证优于无验证。
- 正确工具优于错误工具。
- 根据 observation 修正优于忽略 observation。
- 简洁有效优于重复调用。
- 安全合规优于危险动作。

DPO 数据不要只比较 final answer。否则模型会学会写漂亮总结，但不会学会行动。

## 5. Reward Model：什么时候需要

经典 RLHF 通常是：

```text
SFT -> reward model -> PPO
```

Reward model 用人类偏好数据训练，输入 prompt 和回答，输出一个分数。对 agent 来说，它可以给整条 trajectory 打分。

但 reward model 有两个问题：

- 训练成本高，需要大量偏好数据。
- 容易被模型钻空子，尤其在长轨迹任务中。

所以优先用自动 verifier：

- 代码任务：测试是否通过。
- 网页任务：页面状态或数据库字段是否正确。
- API 任务：返回 JSON 是否匹配。
- 数学/推理任务：答案是否可解析并匹配标准答案。

当任务很难自动判断，例如“调研报告质量”，再考虑 reward model 或 LLM judge，并且要抽样人工复核。

## 6. PPO：经典 RLHF 路线

PPO 会让模型生成回答或轨迹，然后用 reward model / 环境 reward 打分，再更新模型。它通常需要：

- policy model：当前要训练的模型。
- reference model：控制 KL，不让模型偏离太远。
- reward model 或 reward function：给输出打分。
- value model：估计状态价值，降低训练方差。

在 TRL PPOTrainer 文档里，PPO 训练会记录 KL、entropy、reward scores、policy loss、value loss 等指标。对 agent 来说，重点看：

- `objective/kl`：偏离参考模型是否过大。
- `objective/scores`：环境或 reward model 分数。
- `policy/entropy_avg`：策略是否过早塌缩。
- 评估集 success rate：真正重要的指标。

PPO 适合：

- 有成熟 reward model。
- 任务 reward 比较连续，不只是 0/1。
- 团队能承受 value model、KL、采样和分布式训练复杂度。

早期项目不建议直接 PPO。

## 7. GRPO：更适合可验证任务的起点

GRPO 是 PPO 的一个变体。TRL 文档解释的核心流程是：

```text
对同一个 prompt 采样 G 条 completions
-> 用 reward function 给每条打分
-> 在组内用 reward 均值/方差计算相对 advantage
-> 用 KL 约束更新模型
```

直觉是：同一道题、同一个任务下，哪条轨迹更好，就增强哪条。它不一定需要单独的 value model，因此工程上比 PPO 更轻。

Agent GRPO 可以这样做：

```text
prompt: 修复一个 issue
sample 1: 读文件 -> 修改 -> 测试通过      reward = 1.0
sample 2: 直接回答建议                    reward = 0.0
sample 3: 修改错误文件 -> 测试失败         reward = -0.5
sample 4: 删除测试 -> 测试看似通过         reward = -1.0
```

GRPO 特别适合：

- 数学、代码、格式化输出这类可验证任务。
- coding agent：patch 是否通过测试。
- browser agent：最终页面状态是否满足条件。
- API agent：调用链是否得到正确结果。

TRL 的 GRPOTrainer 支持自定义 reward functions，也支持多个 reward function 相加或加权。它还支持通过 `tools` 参数做 agent training，这意味着训练时可以让模型在生成中调用 Python 工具。

## 8. Agent Reward 设计

一个实用 reward 可以拆成：

```text
reward =
  final_success
+ progress_score
+ verification_score
+ valid_action_score
- invalid_action_penalty
- repeat_penalty
- unsafe_penalty
- cost_penalty
- shortcut_penalty
```

代码任务示例：

```python
def coding_agent_reward(traj):
    reward = 0.0
    if traj.patch_applied:
        reward += 0.2
    if traj.tests_ran:
        reward += 0.2
    if traj.tests_passed:
        reward += 1.0
    if traj.modified_unrelated_files:
        reward -= 0.5
    if traj.deleted_tests:
        reward -= 1.0
    if traj.num_steps > 30:
        reward -= 0.2
    return reward
```

网页任务示例：

```python
def browser_agent_reward(traj):
    reward = 0.0
    if traj.reached_target_page:
        reward += 0.2
    if traj.submitted_correct_form:
        reward += 0.4
    if traj.final_state_matches_goal:
        reward += 1.0
    if traj.clicked_dangerous_button:
        reward -= 1.0
    if traj.repeated_same_action:
        reward -= 0.2
    return reward
```

奖励不要太复杂。复杂 reward 更容易互相冲突，也更难 debug。

## 9. Offline 到 Online 的迁移

推荐路线：

```text
阶段 A：只采集，不训练
阶段 B：SFT 学成功轨迹
阶段 C：DPO 学 chosen/rejected
阶段 D：rejection sampling 生成更多成功轨迹
阶段 E：GRPO/PPO 在线优化
```

rejection sampling 很实用：

1. 对同一个任务采样 4 到 16 条轨迹。
2. 用 verifier 选出成功轨迹。
3. 把成功轨迹加入 SFT。
4. 把成功/失败轨迹配成 DPO。

这一步经常比直接 RL 更稳定。

## 10. 训练检查表

训练前：

- 工具 schema 固定了吗？
- trajectory 能完整回放吗？
- verifier 可信了吗？
- eval 集和 train 集隔离了吗？
- 是否有安全边界？

训练中：

- SFT loss 是否下降但 eval 不退化？
- DPO chosen reward 是否高于 rejected？
- GRPO/PPO KL 是否过大？
- 平均步骤数是否异常增加？
- invalid action rate 是否下降？

训练后：

- success rate 是否提升？
- hidden tests 是否通过？
- 是否出现 reward hacking？
- 成本是否可接受？
- 长任务是否更稳，而不是只提升短任务？

如果这些问题答不上来，就不要宣称 agent 变强。
