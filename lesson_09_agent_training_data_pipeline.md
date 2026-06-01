# 第九课：Agent 训练数据管线

## 1. 为什么要单独讲数据管线

Agent 训练失败，很多时候不是算法问题，而是数据管线问题。

常见情况：

- raw log 里混着成功、失败、重复、隐私和伪造 observation。
- SFT 数据让模型学习了失败行为。
- DPO pair 的 chosen/rejected 标签不可靠。
- 工具返回值太长，模型只学到噪声。
- 训练集和评估集泄漏，分数虚高。

所以 agent 数据要先变成可审计、可回放、可转换的中间格式，再生成 SFT、DPO、GRPO/PPO 数据。

## 2. 推荐数据流

完整数据流：

```text
raw execution log
  -> normalize
  -> redact
  -> replay / verify
  -> label success/failure
  -> clean trajectory
  -> build SFT dataset
  -> build DPO dataset
  -> build RL prompt dataset
  -> eval split check
```

每一步都要保存产物，不能只保留最终 JSONL。否则训练出问题时无法回溯。

## 3. Raw Log 应该记录什么

agent 每一步都应记录：

```json
{
  "run_id": "run_20260521_001",
  "task_id": "github_fix_0001",
  "step_index": 3,
  "timestamp": "2026-05-21T10:12:00Z",
  "model": "qwen-agent-sft-v1",
  "observation": "pytest 输出...",
  "assistant_message": {
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {
        "id": "call_3",
        "type": "function",
        "function": {
          "name": "read_file",
          "arguments": "{\"path\":\"src/parser.py\"}"
        }
      }
    ]
  },
  "parsed_action": {
    "name": "read_file",
    "arguments": {"path": "src/parser.py"}
  },
  "tool_result": "文件内容...",
  "tool_error": null,
  "environment_hash": "repo_parser_v1_sha",
  "cost": {
    "input_tokens": 1800,
    "output_tokens": 120
  }
}
```

重要原则：

- `assistant_message` 原样保留，方便排查解析失败。
- `parsed_action` 结构化保存，方便统计工具使用。
- `environment_hash` 保存环境版本，方便复现。
- tool error 不要删，失败恢复样本很有价值。

## 4. Normalize：统一格式

不同框架的日志格式不同。第一步要统一成课程里的 trajectory 格式：

```json
{
  "task_id": "...",
  "task": "...",
  "trajectory": [
    {
      "observation": "...",
      "action": {"name": "...", "arguments": {}},
      "result": "...",
      "error": null
    }
  ],
  "final": "...",
  "final_status": "success",
  "verifier": {
    "name": "pytest",
    "passed": true,
    "details": "4 passed"
  }
}
```

不要在 normalize 阶段做太多主观判断。它只负责格式统一。

## 5. Redact：隐私和安全清洗

必须清洗：

- API key、token、cookie。
- 用户姓名、邮箱、手机号。
- 内部域名、私有仓库 URL。
- 业务数据库内容。
- 浏览器登录态。
- 付款、发邮件、删除数据等危险动作的真实目标。

替换要保留结构：

```text
sk-live-abc123 -> <API_KEY>
alice@example.com -> <EMAIL>
https://internal.company.com -> <INTERNAL_URL>
```

不要直接删除字段，否则模型会学不到上下文结构。

## 6. Verify：自动验证

每条 trajectory 都要经过 verifier：

代码任务：

```text
apply patch -> run tests -> check hidden tests -> label
```

网页任务：

```text
replay actions -> inspect final page/database state -> label
```

API 任务：

```text
replay tool calls in mock server -> compare expected JSON -> label
```

验证结果要写回数据：

```json
{
  "final_status": "failure",
  "failure_type": "tests_failed",
  "verifier_details": "test_empty_input still failing"
}
```

## 7. SFT 数据怎么生成

适合放进 SFT：

- 成功轨迹。
- 中途失败但最终恢复的轨迹。
- 明确拒绝危险请求的轨迹。
- 发现信息不足并正确说明限制的轨迹。

不适合直接放进 SFT：

- 最终失败且没有恢复。
- 工具调用无效但模型继续假装成功。
- 删除测试、绕过检查、伪造结果。
- 长时间重复同一动作。

转换时要保留 tool role：

```json
{
  "messages": [
    {"role": "user", "content": "任务..."},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\":\"src/parser.py\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "Result: ..."},
    {"role": "assistant", "content": "已完成。"}
  ]
}
```

## 8. DPO 数据怎么生成

同一个 task 下的轨迹最适合配 pair：

```text
success trajectory > failure trajectory
verified trajectory > unverified final answer
short valid trajectory > long repeated trajectory
safe refusal > unsafe action
```

自动生成 pair 时要避免标签太弱：

```text
chosen reward = 0.8, rejected reward = 0.7
```

这种 pair 信号不强。优先选差距大的：

```text
chosen reward = 1.0, rejected reward <= 0.0
```

## 9. RL Prompt 数据怎么生成

GRPO/PPO 不需要完整答案作为标签，而需要 prompt 和环境元数据：

```json
{
  "task_id": "github_fix_0001",
  "prompt": "修复 parser 空输入导致的测试失败。",
  "environment": "docker://parser_repo_v1",
  "max_steps": 20,
  "verifier": "pytest tests/test_parser.py -q"
}
```

关键是环境可复现，reward function 能读取环境状态。

## 10. 数据版本管理

每次训练都要记录：

```text
dataset_name: agent_sft_v3
source_runs: run_20260501 到 run_20260520
num_tasks: 1200
num_trajectories: 4800
success_rate_raw: 0.31
filter_rules: remove repeated action > 5, remove secret leaks
train_eval_split: by task_id
```

split 必须按 task_id 分，而不是按 trajectory 分。否则同一任务的成功轨迹在 train，失败轨迹在 eval，会造成泄漏。
