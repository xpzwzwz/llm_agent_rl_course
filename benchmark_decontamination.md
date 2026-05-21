# Benchmark 去污染

## 1. 为什么要去污染？

如果训练数据包含评估任务，评估分数会虚高。

Agent 场景尤其容易污染：

- GitHub issue 公开可见。
- benchmark 讨论出现在网页。
- 标准 patch 被模型预训练见过。
- 同一网页模板被 train/eval 共用。

## 2. 去污染层级

至少检查：

```text
exact task_id overlap
exact prompt overlap
near-duplicate prompt
same source URL / repo / issue
same expected answer
same hidden test target
```

## 3. GitHub / Coding 去污染

记录：

- repo。
- commit。
- issue id。
- PR id。
- patch files。
- test names。

检查：

- train/eval 是否同 repo 同 issue。
- eval patch 是否出现在训练语料。
- 同一 bug 的变体是否跨 split。

## 4. Web / Browser 去污染

记录：

- site。
- page template。
- entity id。
- start URL。
- goal type。

避免：

- 同一订单 ID train/eval 共用。
- 同一页面模板只换 ID 后跨 split。
- final answer 固定文本跨 split。

## 5. RAG 去污染

记录：

- doc_id。
- chunk_id。
- source URI。
- retrieval query。
- answer span。

检查：

- eval answer span 是否在 train 中出现。
- train chunk 是否覆盖 eval question。
- 同一文档不同 chunk 是否跨 split 造成泄漏。

## 6. 时间切分

对公开数据，时间切分很重要：

```text
train: 2025-12-31 前
eval: 2026-01-01 后
```

但时间切分不充分。同一项目旧 issue 可能和新 issue 很像，还需要 near-duplicate 检查。

## 7. 去污染报告

每个 benchmark 记录：

```text
eval_name
eval_version
train_dataset_versions_checked
exact_overlap_count
near_duplicate_count
source_overlap_count
removed_train_samples
remaining_risk
```

没有去污染报告的 benchmark 分数只能作为参考。

