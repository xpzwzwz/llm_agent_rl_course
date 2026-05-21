# 第十课：工具调用格式怎么选

## 1. 格式会影响训练难度

Agent 训练里，工具调用格式不是小事。格式会影响：

- 解析是否稳定。
- SFT loss 是否清晰。
- DPO 比较是否公平。
- RL 时 action space 是否可控。
- 模型是否容易伪造 observation。

常见格式有四类：

- OpenAI-style tool calling。
- ReAct-style text action。
- JSON action。
- XML/tag action。

## 2. OpenAI-style Tool Calling

形式：

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "name": "search_web",
      "arguments": {"query": "SWE-bench benchmark"}
    }
  ]
}
```

优点：

- 结构清晰。
- 易于和现代 API 对接。
- tool role 可以和 assistant role 分开。
- 不容易把工具结果混成模型输出。

缺点：

- 依赖模型和 tokenizer 的 chat template 支持。
- 不同框架字段名可能不同。
- 训练前要确认 assistant-only loss 如何处理 tool calls。

适合生产系统和严肃训练。

## 3. ReAct-style Text Action

形式：

```text
Thought: 我需要先搜索相关资料。
Action: search_web
Action Input: {"query": "WebArena benchmark"}
Observation: ...
```

优点：

- 易读。
- 历史资料多。
- 适合快速原型。

缺点：

- 解析脆弱。
- 模型容易输出多余自然语言。
- `Thought` 可能带来隐私和安全问题。
- Observation 容易被模型伪造。

如果使用 ReAct，建议约束为：

```text
Action: <tool_name>(<json_arguments>)
```

不要让格式自由发挥。

## 4. JSON Action

形式：

```json
{
  "action": "read_file",
  "arguments": {
    "path": "src/parser.py"
  }
}
```

优点：

- 简单。
- 容易解析。
- 和 DPO/RL 数据兼容。

缺点：

- 多轮消息需要自己定义 wrapper。
- 模型可能输出不合法 JSON。
- 需要处理转义和截断。

建议加硬约束：

```text
assistant 每次只能输出一个 JSON object。
不能输出 markdown。
不能编造 observation。
```

## 5. XML / Tag Action

形式：

```xml
<action name="search_web">
{"query": "ToolBench paper"}
</action>
```

优点：

- 比纯 JSON 更容易和自然语言分隔。
- 可读性较好。
- 适合把 final、action、critique 分成不同 tag。

缺点：

- XML 不合法时解析麻烦。
- 嵌套内容容易出错。
- 不如原生 tool calling 标准。

## 6. 训练时怎么选

建议：

```text
生产 API 支持 tool calling -> 用 OpenAI-style tool calling
自己写简单训练闭环 -> 用 JSON action
做论文复现或快速 demo -> 可用 ReAct
需要混合自然语言和结构化块 -> 可用 XML/tag
```

无论哪种格式，都要坚持：

- 一次 assistant 输出最多一个 action 或一个 final。
- 工具结果只能由 environment 写入。
- action 解析失败要作为 invalid action 记录。
- 训练、评估、推理使用同一套格式。

## 7. 格式验证器

每次训练前跑格式验证：

```python
def validate_action(text):
    try:
        obj = json.loads(text)
    except Exception:
        return False, "invalid_json"
    if "action" not in obj:
        return False, "missing_action"
    if "arguments" not in obj:
        return False, "missing_arguments"
    if obj["action"] not in ALLOWED_TOOLS:
        return False, "unknown_tool"
    return True, "ok"
```

格式错误样本不要全删。可以保留为 DPO rejected 或 RL negative reward。

## 8. 防止伪造 Observation

Agent 模型常见坏行为：

```text
Action: run_tests(...)
Observation: all tests passed
Final: done
```

但实际上工具没有执行。

解决方法：

- assistant 只能输出 action/final，不能输出 observation。
- environment 独占 tool role。
- 训练数据里 observation 全部来自日志。
- reward function 只信环境状态，不信模型文本。

