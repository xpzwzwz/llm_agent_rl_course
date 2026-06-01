# 第十课：工具调用格式怎么选

## 1. 格式会影响训练难度

Agent 训练里，工具调用格式不是小事。格式会影响：

- 解析是否稳定。
- SFT loss 是否清晰。
- DPO 比较是否公平。
- RL 时 action space 是否可控。
- 模型是否容易伪造 tool observation。

课程后续统一使用结构化 tool-calling transcript，而不是把动作塞进普通文本前缀。原因很简单：现代 API、chat template 和训练框架都已经支持把 assistant tool call、tool result、最终回答分成不同消息字段；训练时应该利用这个边界。

## 2. 推荐格式：结构化 Tool Calling

一个工具调用回合应该长这样：

```json
{
  "messages": [
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
    {
      "role": "tool",
      "tool_call_id": "call_1",
      "content": "搜索结果..."
    },
    {
      "role": "assistant",
      "content": "WebArena 是一个用于评估网页任务 agent 的基准。"
    }
  ]
}
```

关键点：

- assistant 发起工具调用时，`content` 为 `null`，工具名和参数放在 `tool_calls`。
- environment 写入 `role: "tool"` 消息，并用 `tool_call_id` 对齐上一条调用。
- 最终回答就是普通 assistant `content`，不需要特殊文本前缀。
- 一条 assistant 消息要么是 tool call，要么是最终自然语言回答。

优点：

- 结构清晰，容易验证。
- 易于和现代 API 对接。
- tool role 和 assistant role 分开，loss mask 更明确。
- 不容易把工具结果混成模型输出。
- DPO/RL 里可以比较整条消息轨迹，而不是比较一段脆弱字符串。

需要注意：

- 不同模型的 chat template 对 tool calls 支持不同，训练前要实际 tokenization 抽查。
- OpenAI、Anthropic、Qwen 等生态字段略有差异，进入训练前先 normalize 到一种内部 schema。
- assistant-only loss 应覆盖 assistant tool call 和 final content，但不覆盖 user/tool 内容。

## 3. JSON Action 只适合本地调试

如果本地 runner 暂时没有原生 tool-call API，可以用单个 JSON object 作为调试输出：

```json
{
  "action": "read_file",
  "arguments": {
    "path": "src/parser.py"
  }
}
```

这适合快速验证 parser、工具执行器和 reward function，但不要把它作为课程的主训练格式。落盘训练数据时仍应转换成结构化 messages：

```json
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
}
```

## 4. 文本协议作为反例

把工具调用、工具结果和最终回答都塞进一段 assistant 文本，训练风险很高：

```text
assistant 生成工具调用文本
assistant 生成工具结果文本
assistant 生成最终回答文本
```

问题：

- parser 脆弱，模型多输出一句话就可能失败。
- observation 边界不清，模型容易学会伪造工具结果。
- DPO 比较时很难区分“行动更好”还是“总结写得更像”。
- tool result 如果进了 assistant loss，模型会学环境输出。

这类格式可以用于阅读早期 ReAct 论文或做玩具 demo，但不作为本课程的数据标准。

## 5. 训练时怎么选

建议：

```text
生产 API 或训练框架支持 tool calling -> 用结构化 tool-calling messages
本地最小 runner 暂无原生 tool calling -> 运行时可用 JSON action，落盘时转换成结构化 messages
论文复现旧方法 -> 明确标注为 legacy，不混入主训练数据
```

无论哪种运行时格式，训练数据都要坚持：

- 工具结果只能由 environment 写入。
- assistant 不生成 tool observation。
- 工具调用必须能被 schema 验证。
- 训练、评估、推理使用同一套 normalized schema。

## 6. 格式验证器

训练前至少验证这些约束：

```python
def validate_messages(messages, allowed_tools):
    errors = []
    pending_tool_calls = set()
    for index, message in enumerate(messages):
        role = message.get("role")
        if role == "assistant" and message.get("tool_calls"):
            if message.get("content") is not None:
                errors.append(f"assistant_tool_call_content_not_null_{index}")
            for call in message["tool_calls"]:
                name = call.get("function", {}).get("name")
                if name not in allowed_tools:
                    errors.append(f"unknown_tool_{index}")
                pending_tool_calls.add(call.get("id"))
        elif role == "tool":
            call_id = message.get("tool_call_id")
            if call_id not in pending_tool_calls:
                errors.append(f"orphan_tool_result_{index}")
            pending_tool_calls.discard(call_id)
        elif role == "assistant":
            if not isinstance(message.get("content"), str) or not message["content"].strip():
                errors.append(f"empty_assistant_content_{index}")
    if pending_tool_calls:
        errors.append("missing_tool_result")
    return errors
```

格式错误样本不要全删。可以保留为 DPO rejected、RL negative reward 或数据质量分析集。

## 7. 防止伪造 Observation

Agent 模型常见坏行为是把工具结果写进 assistant 内容里，好像环境已经执行过。解决方法：

- assistant 只能发起 tool call 或给最终回答。
- environment 独占 tool role。
- 训练数据里的 tool content 全部来自真实日志。
- reward function 只信环境状态，不信模型自述。
