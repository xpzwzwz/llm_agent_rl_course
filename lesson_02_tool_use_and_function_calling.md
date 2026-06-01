# 第二课：工具调用和 Function Calling

## 1. 工具调用是什么

工具调用是让模型输出结构化 action，而不是直接输出自然语言。

例如搜索工具：

```json
{
  "name": "search_web",
  "description": "Search the web for current information.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string"}
    },
    "required": ["query"]
  }
}
```

模型应该输出：

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_1",
      "type": "function",
      "function": {
        "name": "search_web",
        "arguments": "{\"query\":\"WebArena benchmark LLM agents success rate\"}"
      }
    }
  ]
}
```

而不是：

```text
我会搜索 WebArena benchmark LLM agents success rate。
```

## 2. 工具调用训练的核心

工具调用训练不是让模型背 JSON。真正要学的是三件事：

- 什么时候该用工具。
- 该用哪个工具。
- 工具结果回来后如何继续。

一个好的训练样本应该包含工具返回值：

```json
{
  "task": "查找 ToolBench 是什么。",
  "steps": [
    {
      "observation": "用户要求查找 ToolBench。",
      "action": {
        "name": "search_web",
        "arguments": {"query": "ToolBench ToolLLM paper"}
      },
      "result": "ToolBench is a benchmark for tool learning..."
    },
    {
      "action": {
        "name": "open_url",
        "arguments": {"url": "https://arxiv.org/abs/2307.16789"}
      },
      "result": "论文摘要..."
    }
  ],
  "final": "ToolBench 是..."
}
```

只给 action，不给 result，模型学不到“观察结果后怎么继续”。

## 3. ToolBench 的启发

ToolBench / ToolLLM 的价值在于把大量真实 API 转成工具学习任务。它强调的不是单个函数，而是“用户指令 -> 工具选择 -> API 调用链 -> 最终回答”。

这给训练 agent 一个重要启发：

```text
工具数据应该覆盖调用链，而不是孤立函数。
```

真实任务经常需要多个工具组合：

```text
search_web -> open_url -> parse_table -> calculate -> final
```

## 4. 常见错误

工具调用模型常见问题：

- 工具幻觉：调用不存在的工具。
- 参数幻觉：编造 URL、文件名、ID。
- 过度调用：明明可以回答，却不断搜索。
- 忽略结果：工具返回失败，模型仍按成功处理。
- 重复调用：同一个查询反复执行，没有新信息。
- 提前结束：没有验证就给最终答案。

训练数据里应该保留一部分失败和恢复样本。例如：

```json
[
  {"role": "assistant", "content": null, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "open_url", "arguments": "{\"url\":\"...\"}"}}]},
  {"role": "tool", "tool_call_id": "call_1", "content": "404 Not Found"},
  {"role": "assistant", "content": null, "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "search_web", "arguments": "{\"query\":\"官方页面\"}"}}]}
]
```

## 5. 工具 Schema 设计原则

工具 schema 会直接影响模型表现。建议：

- 名字短而明确，例如 `search_web`、`read_file`、`run_tests`。
- 参数类型清楚，少用自由文本大字段。
- 枚举值用固定选项，不要让模型猜。
- 返回值结构稳定，避免同一个工具每次返回完全不同格式。
- 对危险工具加权限边界，例如文件写入、删除、付款、发邮件。

工具越稳定，训练越容易。
