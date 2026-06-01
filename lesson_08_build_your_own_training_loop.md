# 第八课：搭建你自己的 Agent 训练闭环

## 1. 最小闭环

一个最小 agent 训练闭环是：

```text
任务集 -> agent 执行 -> 记录 trajectory -> 自动验证 -> 生成训练数据 -> 微调 -> 评估
```

不要一开始追求复杂算法。先让这条链路跑通。

## 2. 目录建议

可以按这个结构组织项目：

```text
agent_training/
  tasks/
    train.jsonl
    eval.jsonl
  trajectories/
    raw/
    cleaned/
  rewards/
    validators.py
  datasets/
    sft.jsonl
    dpo.jsonl
  runs/
    eval_reports/
```

每条任务都要有稳定 ID，方便追踪：

```json
{
  "task_id": "github_bugfix_0001",
  "task": "修复 parser 空输入 bug。",
  "environment": "docker://repo_parser_v1",
  "success_check": "pytest tests/test_parser.py::test_empty_input"
}
```

## 3. 第一版不要做在线 RL

推荐第一版：

1. 用现有模型跑任务，采集轨迹。
2. 自动验证成功和失败。
3. 人工抽查一部分轨迹。
4. 用成功轨迹做 SFT。
5. 用成功/失败轨迹做 DPO。
6. 在固定 eval 集上比较。

只有当 SFT/DPO 已经稳定，且 reward 自动验证可信，再上在线 RL。

## 4. 训练数据生成

SFT 样本可以这样转换：

```json
{
  "messages": [
    {"role": "user", "content": "修复 parser 空输入 bug。"},
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "read_file",
            "arguments": "{\"path\":\"src/parser.py\"}"
          }
        }
      ]
    },
    {"role": "tool", "tool_call_id": "call_1", "content": "文件内容..."},
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_2",
          "type": "function",
          "function": {
            "name": "run_tests",
            "arguments": "{\"command\":\"pytest -q\"}"
          }
        }
      ]
    },
    {"role": "tool", "tool_call_id": "call_2", "content": "passed"},
    {"role": "assistant", "content": "测试通过。"}
  ]
}
```

DPO 样本可以这样转换：

```json
{
  "prompt": "修复 parser 空输入 bug。",
  "chosen": [
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\":\"src/parser.py\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "文件内容..."},
    {"role": "assistant", "content": "passed"}
  ],
  "rejected": [
    {"role": "assistant", "content": "可能是空输入没有处理，请检查 parser.py。"}
  ]
}
```

如果运行时日志来自 JSON action 或其他框架，生成训练数据前先 normalize 成结构化 tool messages。

## 5. 训练后评估

每次训练后至少比较：

- base model。
- SFT model。
- SFT + DPO model。
- 如果有，RL model。

报告格式建议：

```text
model              success_rate   avg_steps   invalid_action_rate   cost
base               0.22           9.8         0.18                  $12
sft                0.36           8.1         0.07                  $10
sft_dpo            0.43           7.4         0.05                  $9
```

不要只看成功率。步骤数、非法动作率和成本同样重要。

## 6. 下一步

当最小闭环稳定后，再扩展：

- 加更多工具。
- 加更难任务。
- 引入多采样和 verifier。
- 用 rejection sampling 生成更强 SFT 数据。
- 用 GRPO/PPO 做环境内优化。
- 建立长周期回归评估。

真正的 agent 能力来自持续闭环，而不是一次训练。
