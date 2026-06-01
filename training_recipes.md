# 训练配方：SFT、DPO、PPO、GRPO 怎么落地

资料核对日期：2026-05-21。参考 Hugging Face TRL 文档、DPO 论文、DeepSeek-R1/DeepSeekMath 相关资料和 RLHF 经典流程。

## 1. 选择哪条路线

先按任务类型选方法：

```text
只有高质量示范数据 -> SFT
有好/坏轨迹对比 -> SFT + DPO
有自动 verifier，任务可多次采样 -> SFT + DPO + GRPO
有成熟 reward model 和工程资源 -> SFT + Reward Model + PPO
```

对多数 agent 项目，推荐起步路线是：

```text
SFT -> DPO -> rejection sampling -> GRPO
```

## 2. SFT 配方

### 输入

- 成功 trajectory。
- 失败后成功恢复的 trajectory。
- 少量普通指令数据，防止模型只会 agent 格式。

### 输出格式

使用 conversational messages：

```json
{
  "messages": [
    {"role": "system", "content": "你是网页 agent，可用工具 search_web, open_url。"},
    {"role": "user", "content": "查找 WebArena 是什么。"},
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "search_web",
            "arguments": "{\"query\":\"WebArena benchmark LLM agents\"}"
          }
        }
      ]
    },
    {"role": "tool", "tool_call_id": "call_1", "content": "搜索结果..."},
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_2",
          "type": "function",
          "function": {
            "name": "open_url",
            "arguments": "{\"url\":\"https://webarena.dev/\"}"
          }
        }
      ]
    },
    {"role": "tool", "tool_call_id": "call_2", "content": "WebArena 项目页内容..."},
    {"role": "assistant", "content": "WebArena 是..."}
  ]
}
```

### 训练要点

- loss 只算 assistant 消息，不算 user/tool 内容。
- tool calls 和 tool responses 要保留结构。
- 同一工具只保留一种参数风格。
- 每条样本必须能解释为什么结束。
- 长轨迹可以切成多个子任务训练。

### 最小伪代码

```python
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer

dataset = load_dataset("json", data_files="datasets/agent_sft.jsonl", split="train")

args = SFTConfig(
    output_dir="runs/agent-sft",
    assistant_only_loss=True,
    learning_rate=1e-5,
    max_length=8192,
)

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-7B-Instruct",
    args=args,
    train_dataset=dataset,
)
trainer.train()
```

如果用 LoRA，可以把学习率提高到 `1e-4` 左右，并使用 PEFT 配置。

## 3. DPO 配方

### 输入

DPO 需要 preference pair：

```json
{
  "prompt": "修复 parser 空输入导致的测试失败。",
  "chosen": [
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "run_tests", "arguments": "{\"command\":\"pytest -q\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "FAILED"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\":\"src/parser.py\"}"}}]},
    {"role": "tool", "tool_call_id": "call_2", "content": "文件内容..."},
    {"role": "assistant", "content": "已修复。"}
  ],
  "rejected": [
    {"role": "assistant", "content": "可能是 parser.py 的问题，建议检查空输入。"}
  ]
}
```

### Pair 构造规则

优先级从高到低：

1. verifier 成功的轨迹优于失败轨迹。
2. hidden tests 通过优于只通过 visible tests。
3. 有验证优于无验证。
4. 有恢复策略优于重复无效动作。
5. 少量有效步骤优于大量无效步骤。
6. 安全动作优于危险动作。

### 最小伪代码

```python
from datasets import load_dataset
from trl import DPOConfig, DPOTrainer

dataset = load_dataset("json", data_files="datasets/agent_dpo.jsonl", split="train")

args = DPOConfig(
    output_dir="runs/agent-dpo",
    learning_rate=5e-7,
    beta=0.1,
    max_length=8192,
)

trainer = DPOTrainer(
    model="runs/agent-sft",
    ref_model=None,
    args=args,
    train_dataset=dataset,
)
trainer.train()
```

### 常见问题

- `chosen` 和 `rejected` 差异太小：信号弱，训练慢。
- pair 里混入错误标签：模型会学坏偏好。
- 只比较 final：模型会学会写总结，不会学会行动。
- beta 太大：模型过度贴近参考模型，学不动。
- beta 太小：模型偏移过大，格式可能崩。

## 4. Reward Model 配方

当 verifier 不够覆盖时，可以训练 reward model。

### 输入

```json
{
  "prompt": "完成网页任务：找到订单状态。",
  "chosen": "打开订单页 -> 搜索订单号 -> 读取状态 -> final",
  "rejected": "搜索失败 -> 猜测状态 -> final"
}
```

### 输出

Reward model 接收 prompt + trajectory，输出一个标量分数。

### 适用场景

- 调研报告质量。
- 客服处理质量。
- 多约束复杂任务。
- 自动 verifier 只能覆盖一部分成功条件。

### 风险

Reward model 不是事实裁判。它会继承偏好数据里的偏见，也可能被模型学会欺骗。重要任务要保留人工抽检和规则 verifier。

## 5. PPO 配方

PPO 是经典 RLHF 路线：

```text
policy model 生成轨迹
reward model / environment 打分
value model 估计价值
KL 控制 policy 不偏离 reference model
PPO 更新 policy
```

### 适用条件

- 你已经有稳定 SFT 模型。
- reward model 或环境 reward 可靠。
- 有足够算力处理 rollout。
- 能监控 KL、entropy、value loss 和 success rate。

### 最小伪代码

```python
from trl.experimental.ppo import PPOConfig, PPOTrainer

args = PPOConfig(
    output_dir="runs/agent-ppo",
    learning_rate=3e-6,
    total_episodes=10000,
    num_ppo_epochs=1,
)

trainer = PPOTrainer(
    args=args,
    processing_class=tokenizer,
    model=policy_model,
    ref_model=reference_model,
    reward_model=reward_model,
    value_model=value_model,
    train_dataset=prompt_dataset,
)

trainer.train()
```

### 监控指标

- KL 过高：模型偏离太快，容易格式崩。
- entropy 过低：策略塌缩，探索不足。
- reward 上升但 eval 不升：reward hacking。
- 平均步骤数暴涨：模型可能在刷过程奖励。

## 6. GRPO 配方

GRPO 更适合有自动 verifier 的任务。核心是同一 prompt 采样多条轨迹，在组内比较。

### 输入

训练集只需要 prompt 和必要元数据：

```json
{
  "prompt": "修复 parser 空输入导致的测试失败。",
  "repo_id": "parser_repo_v1",
  "test_command": "pytest tests/test_parser.py -q"
}
```

### Reward Function

```python
def reward_func(prompts, completions, repo_id, test_command, **kwargs):
    rewards = []
    for prompt, completion, rid, cmd in zip(prompts, completions, repo_id, test_command):
        traj = run_completion_in_sandbox(rid, completion)
        reward = 0.0
        if traj.patch_applied:
            reward += 0.2
        if traj.tests_ran:
            reward += 0.2
        if traj.tests_passed(cmd):
            reward += 1.0
        if traj.deleted_tests:
            reward -= 1.0
        if traj.invalid_tool_calls > 0:
            reward -= 0.2
        rewards.append(reward)
    return rewards
```

### 最小伪代码

```python
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer

dataset = load_dataset("json", data_files="datasets/agent_grpo_prompts.jsonl", split="train")

args = GRPOConfig(
    output_dir="runs/agent-grpo",
    learning_rate=1e-6,
    num_generations=8,
    max_prompt_length=4096,
    max_completion_length=4096,
)

trainer = GRPOTrainer(
    model="runs/agent-dpo",
    args=args,
    reward_funcs=reward_func,
    train_dataset=dataset,
)
trainer.train()
```

### 训练要点

- 每个 prompt 要采样多条，组内 reward 才有比较意义。
- reward 要能区分部分成功和完全失败。
- 对删除测试、绕过检查、伪造工具结果给强惩罚。
- 保留 KL 约束，防止模型偏离参考策略。
- 用独立 eval 环境评估，不要只看训练 reward。

## 7. Rejection Sampling 配方

这是最实用的中间阶段：

```text
对每个 prompt 采样 N 条轨迹
-> verifier 打分
-> 成功轨迹加入 SFT
-> 成功/失败组成 DPO
-> 重新训练
```

伪代码：

```python
for task in tasks:
    samples = [agent.run(task) for _ in range(8)]
    scored = [(traj, verifier.score(traj)) for traj in samples]
    successes = [traj for traj, score in scored if score >= 1.0]
    failures = [traj for traj, score in scored if score < 1.0]

    for traj in successes:
        write_sft(traj)

    for good in successes:
        for bad in failures[:2]:
            write_dpo(task.prompt, chosen=good, rejected=bad)
```

这一步成本低，收益通常很高。

## 8. 常见训练事故

### 训练后不会调用工具

原因：

- SFT 数据里工具调用太少。
- chat template 没正确表达 tool role。
- loss 算到了 tool 返回值，模型学会伪造 observation。

处理：

- 增加真实工具调用轨迹。
- 检查 tokenizer/chat template。
- 只对 assistant action/final 算 loss。

### Reward 上升，成功率不升

原因：

- reward 被钻空子。
- 训练任务泄漏。
- 评估器太弱。

处理：

- 加 hidden tests。
- 把可疑高分轨迹人工抽查。
- 给 shortcut 行为负奖励。

### 模型变啰嗦，步骤变多

原因：

- progress reward 太高。
- 没有 cost penalty。
- 训练数据里重复轨迹多。

处理：

- 降低过程奖励。
- 增加 step/cost penalty。
- 清洗重复无效动作。

### 模型格式崩

原因：

- RL 学习率太大。
- KL 太弱。
- DPO beta 太小。
- 训练数据格式混乱。

处理：

- 降学习率。
- 加强 KL。
- 回到 SFT checkpoint。
- 统一工具 schema。

## 9. 最小实验计划

第一周：

- 选 100 个任务。
- 跑现有模型采集轨迹。
- 写 verifier。
- 建 eval 集。

第二周：

- 清洗 100 到 300 条 SFT 样本。
- 训练 LoRA SFT。
- 比较 base 和 SFT。

第三周：

- 对每个任务采样 4 到 8 条轨迹。
- 构造 DPO pair。
- 训练 DPO。
- 跑固定 eval。

第四周：

- 用 rejection sampling 扩数据。
- 如果 verifier 稳定，尝试 GRPO。
- 分析 reward hacking 和失败类型。
