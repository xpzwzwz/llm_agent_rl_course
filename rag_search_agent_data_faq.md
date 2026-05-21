# RAG / Search Agent 数据 FAQ

## 1. 检索结果要不要进训练目标？

检索结果是 observation，不应该让模型学习生成。

模型应该学习：

- 什么时候检索。
- 怎么改写 query。
- 如何选择来源。
- 如何基于来源回答。

## 2. Citation 怎么标？

每个结论最好能对应来源：

```json
{
  "claim": "GRPO 适合可验证任务。",
  "source_id": "doc_003",
  "quote_span": "GRPO 适合有 verifier 的任务"
}
```

训练时可以让模型输出引用，但 source 原文不应被编造。

## 3. Answer correctness 和 source faithfulness 要分开吗？

要分开。

一个回答可能：

- 答案正确但没引用来源。
- 引用了来源但误读。
- 来源正确但答案过度推断。

DPO pair 可以分别构造：

```text
faithful answer > unsupported answer
correct answer with citation > correct answer without citation
```

## 4. Retrieved context 太长怎么办？

保留：

- query。
- top-k doc ids。
- 每个 doc 的摘要。
- raw_ref。
- 截断标记。

不要把大量无关 context 直接塞进 SFT。

## 5. Query rewrite 轨迹要不要保留？

要。Search agent 很多能力来自 query 改写。

好轨迹：

```text
初始 query 无结果
-> 提取关键实体
-> 改写 query
-> 找到官方来源
```

这种失败恢复适合进 SFT。

## 6. RAG 数据常见风险

- 来源过期。
- 搜索结果被 SEO 污染。
- prompt injection 来自网页。
- citation 指向不支持结论的位置。
- 检索语料和 eval 泄漏。

