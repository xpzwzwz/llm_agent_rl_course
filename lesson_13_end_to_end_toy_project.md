# 第十三课：端到端 Toy Project

## 1. 项目目标

这个 toy project 不追求训练强模型，而是跑通完整闭环：

```text
任务 -> 工具环境 -> 采集轨迹 -> SFT 数据 -> DPO 数据 -> verifier -> 评估报告
```

建议场景：文件系统问答 agent。

Agent 可用工具：

- `list_files(path)`
- `read_file(path)`
- `search_text(query)`

任务示例：

```text
在项目文档里找到 GRPO 适合什么场景。
```

## 2. 项目目录

```text
toy_agent_training/
  env/
    corpus/
      lesson_06.md
      training_recipes.md
    tools.py
    verifier.py
  data/
    tasks.jsonl
    trajectories_raw.jsonl
    sft.jsonl
    dpo.jsonl
  reports/
    eval_base.md
    eval_sft.md
```

## 3. 任务集

`tasks.jsonl`：

```json
{"task_id":"doc_001","prompt":"找到 GRPO 适合什么任务。","answer_contains":["可验证","多条","reward"]}
{"task_id":"doc_002","prompt":"找出 DPO 需要什么数据格式。","answer_contains":["prompt","chosen","rejected"]}
{"task_id":"doc_003","prompt":"说明 reward hacking 的一个例子。","answer_contains":["删除测试","伪造","重复"]}
```

先做 20 条任务就够。

## 4. 工具设计

工具返回值要短而稳定：

```python
def list_files(path="."):
    return ["lesson_06.md", "training_recipes.md", "glossary.md"]

def read_file(path):
    text = open(f"env/corpus/{path}").read()
    return text[:3000]

def search_text(query):
    matches = []
    for path in corpus_files:
        for line_no, line in enumerate(open(path), start=1):
            if query.lower() in line.lower():
                matches.append({"path": path, "line": line_no, "text": line.strip()})
    return matches[:10]
```

不要让工具一次返回太多内容。训练早期重点是学会选择和迭代。

## 5. 采集轨迹

每条任务采样 4 次：

```text
for task in tasks:
    for seed in range(4):
        trajectory = run_agent(task, seed)
        score = verifier(task, trajectory.final)
        save_raw(task, trajectory, score)
```

verifier 可以很简单：

```python
def verify(task, final_answer):
    return all(term in final_answer for term in task["answer_contains"])
```

这个 verifier 不完美，但足够跑通流程。

## 6. 生成 SFT

筛选：

```text
score == 1.0
invalid_action_count == 0
num_steps <= 8
```

转换成 messages：

```json
{
  "messages": [
    {"role":"user","content":"找到 GRPO 适合什么任务。"},
    {"role":"assistant","content":null,"tool_calls":[{"id":"call_1","type":"function","function":{"name":"search_text","arguments":"{\"query\":\"GRPO\"}"}}]},
    {"role":"tool","tool_call_id":"call_1","content":"[{\"path\":\"lesson_06.md\",\"line\":237,\"text\":\"GRPO...\"}]"},
    {"role":"assistant","content":null,"tool_calls":[{"id":"call_2","type":"function","function":{"name":"read_file","arguments":"{\"path\":\"lesson_06.md\"}"}}]},
    {"role":"tool","tool_call_id":"call_2","content":"..."},
    {"role":"assistant","content":"GRPO 适合有自动 verifier 的可验证任务..."}
  ]
}
```

## 7. 生成 DPO

同一任务中：

```text
最高分轨迹 -> chosen
最低分轨迹 -> rejected
```

如果多条都成功，选择步骤更少且引用更准的作为 chosen。

```json
{
  "prompt": "找到 GRPO 适合什么任务。",
  "chosen": [
    {"role":"assistant","content":null,"tool_calls":[{"id":"call_1","type":"function","function":{"name":"search_text","arguments":"{\"query\":\"GRPO\"}"}}]},
    {"role":"tool","tool_call_id":"call_1","content":"GRPO 适合可验证任务..."},
    {"role":"assistant","content":"GRPO 适合可验证任务..."}
  ],
  "rejected": [
    {"role":"assistant","content":"GRPO 是一种强化学习算法。"}
  ]
}
```

## 8. 评估报告模板

每个模型都输出：

```text
model: base
num_tasks: 20
success_rate: 0.35
invalid_action_rate: 0.12
avg_steps: 5.8
avg_tokens: 1800

top_failures:
- doc_004: premature_final
- doc_009: wrong_file
- doc_012: invalid_json

examples:
- best trajectory: ...
- worst high-confidence failure: ...
```

## 9. Toy Project 的价值

这个项目很小，但能验证所有关键部件：

- 工具协议是否稳定。
- trajectory 是否能记录。
- SFT 数据是否能生成。
- DPO pair 是否合理。
- verifier 是否能区分成功失败。
- 评估报告是否能解释模型变化。

跑通这个 toy project 后，再换成浏览器、GitHub 或业务 API 环境。

## 10. 下一步扩展

扩展路线：

1. 把 corpus 换成真实项目文档。
2. 加 `open_url` 或 `read_repo_file` 工具。
3. 加 100 到 500 条任务。
4. 用 rejection sampling 扩 SFT/DPO。
5. 用 GRPO 让模型在 verifier 上继续优化。
