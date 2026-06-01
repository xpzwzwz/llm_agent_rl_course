# 数据 Before / After 示例

这份文档展示坏数据如何改成好数据。

## 1. SFT 示例

Before：

```json
{
  "messages": [
    {"role": "user", "content": "修复测试失败。"},
    {"role": "assistant", "content": "我认为问题在 parser.py，建议你检查。"}
  ]
}
```

问题：

- 没有工具调用。
- 没有验证。
- 只是建议。

After：

```json
{
  "messages": [
    {"role": "user", "content": "修复测试失败。"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "run_tests", "arguments": "{\"command\":\"pytest -q\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "FAILED test_empty_input"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "read_file", "arguments": "{\"path\":\"src/parser.py\"}"}}]},
    {"role": "tool", "tool_call_id": "call_2", "content": "def parse(text): return text.split(',')"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_3", "type": "function", "function": {"name": "edit_file", "arguments": "{\"path\":\"src/parser.py\",\"patch\":\"if not text: return []\"}"}}]},
    {"role": "tool", "tool_call_id": "call_3", "content": "edited"},
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_4", "type": "function", "function": {"name": "run_tests", "arguments": "{\"command\":\"pytest -q\"}"}}]},
    {"role": "tool", "tool_call_id": "call_4", "content": "4 passed"},
    {"role": "assistant", "content": "已修复并通过测试。"}
  ]
}
```

## 2. DPO 示例

Before：

```json
{
  "prompt": "找到 GRPO 适合什么任务。",
  "chosen": "GRPO 是一种很强大的算法，应用广泛。",
  "rejected": "GRPO 适合可验证任务。"
}
```

问题：

- chosen 更空泛。
- rejected 更准确。

After：

```json
{
  "prompt": "找到 GRPO 适合什么任务。",
  "chosen": [
    {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "search_text", "arguments": "{\"query\":\"GRPO\"}"}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": "GRPO 适合可验证任务..."},
    {"role": "assistant", "content": "GRPO 适合有 verifier 的任务，例如数学、代码、网页状态检查。"}
  ],
  "rejected": [
    {"role": "assistant", "content": "GRPO 是一种很强大的算法，应用广泛。"}
  ]
}
```

## 3. Trajectory 示例

Before：

```json
{
  "task": "查询订单状态。",
  "steps": [
    {"action": "open_page", "result": "页面打开了"}
  ],
  "final": "订单已发货。"
}
```

问题：

- 没有订单号。
- 没有 provenance。
- 没有 verifier。
- final 可能是猜的。

After：

```json
{
  "task_id": "order_001",
  "task": "查询订单 #123 的物流状态。",
  "steps": [
    {
      "observation": "订单页面有搜索框。",
      "action": {"name": "type", "arguments": {"selector": "#search", "text": "123"}},
      "result": "搜索框已输入 123",
      "provenance": {"source_type": "browser", "trusted": true}
    },
    {
      "observation": "页面显示订单 #123。",
      "action": {"name": "read_text", "arguments": {"selector": "#shipping-status"}},
      "result": "已发货"
    }
  ],
  "final": "订单 #123 当前状态是已发货。",
  "verifier": {"passed": true, "type": "dom_text", "expected": "已发货"}
}
```
