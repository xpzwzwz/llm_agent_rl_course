# Agent Trajectory 数据构造手册

资料核对日期：2026-05-21。参考 ToolBench、WebArena、SWE-bench、AgentGym、OpenHands/browser-use 轨迹思路，以及 agent prompt injection / sandbox 相关资料。

## 1. Trajectory 是 Agent 数据核心

Agent 数据的基本单位不是问答，而是：

```text
task -> observation -> action -> result -> ... -> final -> verifier
```

每条 trajectory 必须能回答：

- 任务是什么？
- 模型看到了什么？
- 模型做了什么？
- 工具真实返回了什么？
- 环境最终状态是什么？
- verifier 为什么判成功或失败？

## 2. Raw Log 到 Trajectory

Raw log 字段：

```json
{
  "run_id": "...",
  "task_id": "...",
  "step_index": 3,
  "assistant_output_raw": "...",
  "parsed_action": {"name": "read_file", "arguments": {"path": "src/a.py"}},
  "tool_result_raw": "...",
  "tool_error": null,
  "timestamp": "...",
  "model_checkpoint": "...",
  "environment_version": "..."
}
```

Trajectory 字段：

```json
{
  "task_id": "...",
  "task": "...",
  "steps": [
    {
      "observation": "...",
      "action": {"name": "...", "arguments": {}},
      "result": "...",
      "error": null
    }
  ],
  "final": "...",
  "verifier": {"passed": true, "details": "..."}
}
```

不要丢 raw log。trajectory 是训练视图，raw log 是审计视图。

## 3. Provenance

每个 observation 和 result 都要标来源：

```json
{
  "source_type": "web_page",
  "source_uri": "https://example.com/orders",
  "trusted": false,
  "captured_at": "2026-05-21T10:00:00Z"
}
```

来源类型：

- `user_input`
- `system_instruction`
- `tool_result`
- `web_page`
- `repo_file`
- `test_output`
- `verifier_only`

模型可见内容不能混入 `verifier_only`。

## 4. Replay

每条 agent 数据都应尽量可回放。

记录：

```text
environment snapshot
random seed
tool versions
model checkpoint
initial state
step actions
final verifier
```

每批数据要统计：

```text
replay_success_rate
replay_mismatch_rate
environment_missing_rate
```

不可回放数据可以用于分析，但不宜作为高权重训练数据。

## 5. Tool Result 摘要

长 tool result 要摘要，但摘要必须忠实。

保留：

- 关键错误。
- 文件名/URL/字段名。
- 可执行下一步的信息。
- 截断标记。
- raw result 引用。

不要摘要成：

```text
工具返回了一些相关信息。
```

这对训练没有用。

## 6. 失败类型

每条失败轨迹必须打标签：

```text
invalid_action
wrong_tool
bad_arguments
tool_error_unhandled
ignored_observation
premature_final
unsafe_action
verifier_failed
environment_error
```

失败类型用于：

- DPO rejected 分桶。
- RL negative reward。
- 错误分析。
- 后续数据采集目标。

## 7. Agent 数据 Split

按任务 split：

```text
train_task_ids
eval_task_ids
test_task_ids
```

不要按 trajectory split。

对 GitHub：

- 相同 repo 的相似 issue 要小心泄漏。
- patch 相关文件不能泄漏到 prompt。

对网页：

- 相同页面模板不同 ID 可能过于相似。
- eval 需要保留新页面结构。

## 8. 安全数据

Agent 数据要包含安全场景：

- 网页 prompt injection。
- 不可信 tool result。
- secret redaction。
- 越权工具请求。
- source conflict。

正确轨迹应展示：

```text
识别不可信来源 -> 不执行恶意指令 -> 继续完成原任务或安全拒绝
```

安全失败轨迹可作为 DPO rejected 或 RL negative reward。

## 9. Dataset Card

每个 agent trajectory dataset 应该有 dataset card：

```text
数据来源
任务类型
工具列表
环境版本
采集模型
成功率
失败类型分布
安全过滤规则
隐私清洗规则
train/eval split 方法
已知限制
```

没有 dataset card 的 agent 数据，很难长期维护。

