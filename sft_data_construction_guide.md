# SFT 数据构造手册

资料核对日期：2026-05-21。参考 RLHF Book、Hugging Face Alignment Handbook、TRL SFTTrainer 文档、OpenAI Model Spec 的标注规范思路，以及课程 toy project。

## 1. SFT 数据的目标

SFT 不是让模型“变聪明”，而是让模型学会目标行为分布：

```text
给定 prompt/history -> 生成合格 assistant 输出
```

对 agent 来说，合格输出包括：

- 正确结构化 tool call。
- 正确工具选择。
- 根据 observation 继续。
- 必要时验证。
- 合理最终回答。

## 2. 样本格式

推荐 messages 格式：

```json
{
  "messages": [
    {"role": "system", "content": "你是代码 agent，可用工具 read_file, run_tests。"},
    {"role": "user", "content": "修复测试失败。"},
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_1",
          "type": "function",
          "function": {
            "name": "run_tests",
            "arguments": "{\"command\":\"pytest -q\"}"
          }
        }
      ]
    },
    {"role": "tool", "tool_call_id": "call_1", "content": "FAILED test_empty_input"},
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
    {"role": "tool", "tool_call_id": "call_2", "content": "def parse(text): ..."},
    {"role": "assistant", "content": "已修复并通过测试。"}
  ]
}
```

关键：

- assistant 的 tool call 和最终回答是模型要学的。
- `tool` 是环境返回，不应该让模型学习生成。
- `system` 要稳定，不要每条随机变化。

## 3. Assistant-only Loss 检查

训练前必须确认 loss mask：

```text
system: no loss
user: no loss
tool: no loss
assistant tool_calls/final content: loss
```

抽查方法：

1. 对一条样本 apply chat template。
2. 打印 token 和 label。
3. 确认 user/tool token 的 label 是 `-100`。
4. 确认 assistant action/final token 有 label。

如果工具返回也参与 loss，模型可能学会伪造 observation。

## 4. 成功轨迹和恢复轨迹

可以进入 SFT：

```text
成功轨迹
失败后恢复轨迹
安全拒绝轨迹
发现信息不足后诚实说明限制的轨迹
```

谨慎进入 SFT：

```text
部分成功
长轨迹
LLM judge 判好但 verifier 未确认
```

不应进入 SFT：

```text
最终失败且未恢复
伪造工具结果
越权动作
删除测试
重复无效动作
```

## 5. Tool Result 原文还是摘要

保留原文适合：

- 结果短。
- 结果结构化。
- 需要模型学习精确字段。

摘要适合：

- 网页 DOM 很长。
- 测试日志很长。
- 搜索结果很多。

摘要必须保留：

- 来源。
- 关键错误。
- 可执行下一步所需字段。
- 是否截断。

示例：

```json
{
  "source": "pytest",
  "summary": "test_empty_input failed with ValueError",
  "truncated": true,
  "raw_ref": "logs/run_001_step_02.txt"
}
```

## 6. 多轮截断策略

长 trajectory 不能简单从头或从尾截断。

推荐：

- 保留任务原始 prompt。
- 保留最近 K 步。
- 保留关键 milestone。
- 保留最终 verifier 相关步骤。
- 用 state summary 替代很早的普通步骤。

不要截断掉：

- 工具调用对应的 tool result。
- 错误恢复前的错误信息。
- final 前的验证步骤。

## 7. 数据混比

Agent SFT 不应该 100% 都是工具轨迹，否则普通对话能力可能下降。

起步混比：

```text
agent trajectory: 60%
普通指令/问答: 25%
安全拒绝: 10%
格式/工具 schema 小任务: 5%
```

实际比例看评估结果调整。

## 8. SFT 数据审计

每批 SFT 数据记录：

```text
num_samples
avg_messages
avg_assistant_tokens
avg_tool_tokens
tool_role_ratio
success_verified_rate
recovery_trajectory_rate
invalid_action_rate_before_filter
truncation_rate
secret_redaction_count
```

抽查：

- 每 1000 条至少人工看 20 条。
- 每种任务类型至少看 10 条。
- 高 token 样本单独抽查。
