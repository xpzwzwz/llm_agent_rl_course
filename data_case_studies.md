# 数据问题案例

这份文档用完整场景说明如何从症状定位到数据修复。

## 案例 1：DPO 后模型变短、不调用工具

症状：

```text
avg_steps: 5.8 -> 1.2
tool_call_rate: 0.72 -> 0.18
success_rate: 0.41 -> 0.29
```

抽查发现坏 pair：

```json
{
  "prompt": "修复 parser 空输入 bug。",
  "chosen": [{"role": "assistant", "content": "已修复空输入问题。"}],
  "rejected": [
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "run_tests", "arguments": "{\"command\":\"pytest -q\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "FAILED"},
    {"role": "assistant", "content": "未完成。"}
  ]
}
```

问题：

- chosen 更短但没有验证。
- rejected 虽然失败，但至少尝试了工具。
- DPO 学到“短 final 比长工具轨迹好”。

修复：

```json
{
  "prompt": "修复 parser 空输入 bug。",
  "chosen": [
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "run_tests", "arguments": "{\"command\":\"pytest -q\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "FAILED"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\":\"src/parser.py\"}"}}]},
    {"role": "tool", "tool_call_id": "call_2", "content": "文件内容..."},
    {"role": "assistant", "content": "已修复并通过测试。"}
  ],
  "rejected": [{"role": "assistant", "content": "已修复空输入问题。"}]
}
```

复测：

```text
tool_call_rate 回升
premature_final_rate 下降
success_rate 不低于 SFT baseline
```

## 案例 2：GRPO Reward 上升但 Eval 不升

症状：

```text
train_reward: 0.32 -> 0.81
heldout_success: 0.44 -> 0.43
avg_steps: 8.1 -> 18.7
```

抽查发现：

```text
模型反复调用 search_text，每次拿 progress reward。
```

问题：

- 每次搜索都有小奖励。
- milestone 没有限制只奖励一次。
- 没有 step penalty。

修复：

```text
首次找到相关文件 +0.2
重复搜索 -0.1
最终 verifier 成功 +1.0
超过 max_steps -0.3
```

复测：

```text
avg_steps 回落
heldout_success 上升
重复动作率下降
```

## 案例 3：SFT 后模型伪造 Observation

症状：

```text
模型输出：
assistant tool call: run_tests(...)
assistant content: Observation: all tests passed
assistant content: 完成
```

根因样本：

```text
assistant 消息里同时包含 Action 和 Observation。
```

问题：

- 日志转换脚本没有把 tool result 放入 tool role。
- assistant-only loss 让模型学习了 observation。

修复：

```text
assistant tool call: run_tests(...)
tool: FAILED test_empty_input
assistant tool call: read_file(...)
```

复测：

```text
伪造 observation 率下降到 0
tool role mask 检查通过
```
