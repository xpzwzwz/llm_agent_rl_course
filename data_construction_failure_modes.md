# 数据构造问题清单

资料核对日期：2026-05-21。参考 RLHF Book、Hugging Face Alignment Handbook、UltraFeedback/Orca DPO pairs、ToolBench/WebArena/SWE-bench 这类数据和基准，以及课程 toy project 的数据闭环。

这份文档只讲数据问题，不讲训练超参。训练中很多“模型不行”，根因其实是数据坏了。

如果要按数据类型落地，请继续看：

- [SFT 数据构造手册](sft_data_construction_guide.md)
- [Preference / DPO 数据构造手册](preference_data_construction_guide.md)
- [Reward Model 数据构造手册](reward_model_data_guide.md)
- [Agent Trajectory 数据构造手册](agent_trajectory_data_guide.md)
- [数据 Schema 参考](data_schema_reference.md)
- [数据质量 Rubric](data_quality_rubric.md)
- [坏数据案例库](bad_data_examples.md)
- [多阶段 Post-Training 数据策略](multi_stage_data_strategy.md)
- [数据混比和 Curriculum 设计](data_mixture_and_curriculum.md)
- [数据问题排查索引](data_debugging_index.md)
- [数据决策树](data_decision_trees.md)
- [公开数据集导读](public_dataset_reading_guide.md)
- [数据版本变更模板](dataset_change_log_template.md)
- [按角色阅读路线](role_based_reading_guide.md)
- [标注员操作指南](annotation_guideline.md)
- [生产数据回流流程](production_data_feedback_loop.md)
- [业务域数据构造配方](domain_specific_data_recipes.md)
- [数据问题严重级别](data_issue_severity_levels.md)
- [数据构造工作流总览](data_workflow_overview.md)
- [数据问题案例](data_case_studies.md)
- [数据 Before / After 示例](data_before_after_examples.md)
- [数据失败复盘模板](data_failure_postmortem_template.md)
- [数据构造 FAQ](data_construction_faq.md)
- [数据许可和治理 FAQ](legal_and_data_governance_faq.md)
- [多模态 / VLM Agent 数据 FAQ](multimodal_agent_data_faq.md)
- [RAG / Search Agent 数据 FAQ](rag_search_agent_data_faq.md)
- [长上下文数据 FAQ](long_context_data_faq.md)
- [采样和成本策略](sampling_and_cost_strategy.md)
- [Benchmark 去污染](benchmark_decontamination.md)

## 1. SFT 数据常见问题

### 1.1 把失败轨迹当示范

坏数据：

```text
assistant tool call: search_web(...)
tool result: no useful result
assistant content: 可能是因为版本问题。
```

如果这条轨迹没有最终验证成功，不应该直接放进 SFT。否则模型会学会“查不到就猜”。

处理：

- 成功轨迹进入 SFT。
- 失败后成功恢复的轨迹进入 SFT。
- 失败且未恢复的轨迹进入 DPO rejected 或错误分析集。

### 1.2 让模型学习 tool observation

如果训练 loss 算到了 tool message，模型可能学会伪造 observation。

错误：

```text
assistant 生成 Action
assistant 生成 Observation
assistant 生成 Final
```

正确：

```text
assistant 生成 Action
tool/environment 生成 Observation
assistant 生成 Final
```

处理：

- tool role 不算 assistant loss。
- chat template 明确区分 assistant 和 tool。
- 训练前抽样检查 token mask。

### 1.3 轨迹太长但无信息密度

坏轨迹：

```text
search A -> search A -> search A -> open same URL -> open same URL
```

这种数据会让模型学会重复。

处理：

- 去掉连续重复动作。
- 记录 `num_repeated_actions`。
- 重复轨迹可作为 DPO rejected。

### 1.4 工具格式不一致

同一个工具在数据里有多种格式：

```text
search_web({"query":"..."})
{"tool":"search_web","args":{"q":"..."}}
Search[...]
```

模型会学得不稳定。

处理：

- 一个训练 run 只用一种 action 格式。
- 工具名、参数名固定。
- 写格式验证器。

## 2. DPO Pair 常见问题

### 2.1 Chosen 和 Rejected 差异太小

```text
chosen score = 0.8
rejected score = 0.75
```

这种 pair 信号弱，甚至可能是噪声。

处理：

- 优先使用 `1.0 vs 0.0`。
- 或者至少要求 reward gap 大于阈值。
- 弱 pair 单独放低权重数据集。

### 2.2 只比较 Final，不比较 Trajectory

坏 pair：

```json
{
  "chosen": [{"role": "assistant", "content": "已完成。"}],
  "rejected": [{"role": "assistant", "content": "没完成。"}]
}
```

对 agent 来说，这学不到工具使用。

正确 pair 应包含：

```text
assistant tool call -> tool result -> assistant tool call -> tool result -> assistant final answer
```

### 2.3 Rejected 太差

如果 rejected 都是明显胡说，DPO 会很容易，但学不到细粒度偏好。

更好的 rejected：

- 格式正确但没验证。
- 工具选择接近正确但关键步骤错。
- 完成一半但提前 final。
- 通过 visible tests 但 hidden tests 失败。

### 2.4 标签来源不可信

LLM judge 给 chosen/rejected，如果没有 verifier 或人工抽查，很容易偏向长回答、礼貌回答、看似完整的回答。

处理：

- verifier 优先。
- LLM judge 只作为辅助。
- 高分样本抽查。
- 记录 `preference_source`。

## 3. Reward Model 数据问题

### 3.1 偏好数据分布太窄

如果 reward model 只见过短回答，RL 后遇到长 agent 轨迹就可能失效。

处理：

- 偏好数据覆盖不同长度。
- 覆盖成功、部分成功、失败、危险动作。
- 覆盖工具调用、网页、代码等场景。

### 3.2 偏好标准混乱

标注员 A 偏好简洁，标注员 B 偏好详细，reward model 会学到混合噪声。

处理：

- 写标注指南。
- 标注 `preference_reason`。
- 计算一致性。
- 冲突样本进入复审。

### 3.3 Reward Model 学到表面特征

它可能偏好：

- 更长回答。
- 更多项目符号。
- 更自信语气。
- 固定模板。

处理：

- 加入“长但错”作为 rejected。
- 加入“短但正确”作为 chosen。
- 用 verifier 校正偏好。

## 4. Agent 数据特有问题

### 4.1 Observation 不可复现

网页内容、GitHub issue、搜索结果会变。

处理：

- 保存环境快照。
- 保存 URL、页面文本、时间戳。
- 对训练数据保存 tool result 原文或摘要。

### 4.2 环境状态泄漏

训练集中包含 hidden test 输出、标准答案、数据库目标状态。

处理：

- 区分 model-visible observation 和 verifier-only metadata。
- hidden 信息只能给 verifier。
- 数据生成时强制字段隔离。

### 4.3 同一任务泄漏到评估集

同一 task 的不同 trajectory 分别进入 train 和 eval，会导致评估虚高。

处理：

- 按 `task_id` split。
- 不按 trajectory 随机 split。
- 相似任务也要去重。

### 4.4 Synthetic Data 过度模板化

合成数据常见问题：

- 所有任务一个句式。
- 工具调用路径过于理想。
- 没有真实错误和恢复。
- final 总是固定模板。

处理：

- 混入真实轨迹。
- 合成后用 verifier 和人工抽查。
- 加入失败恢复样本。
- 控制模板重复率。

## 5. 数据审计表

每批数据训练前都要统计：

```text
num_tasks
num_trajectories
success_rate
avg_steps
avg_tokens
invalid_action_rate
repeated_action_rate
tool_error_rate
train_eval_task_overlap
secret_leak_count
chosen_rejected_reward_gap_avg
```

如果这些指标没有记录，这批数据不应该进入正式训练。

## 6. 额外长尾问题

### 6.1 Pair 来源和 Judge 来源相关

如果回答由模型 A 生成，judge 也是模型 A 或同家族模型，偏好可能更像“风格相似度”。

处理：

- 记录 generator model 和 judge model。
- 不同家族交叉评估。
- 对 judge 高分样本抽查。

### 6.2 数据里混入不可见 verifier 信息

例如把 hidden test 结果、标准答案、数据库目标状态放进 prompt 或 observation。

处理：

- 字段分为 `model_visible` 和 `verifier_only`。
- 构造训练样本时只读取 `model_visible`。
- 写单元测试检查 hidden 字段不会进入 prompt。

### 6.3 失败样本缺少失败原因

只记录 `failure`，不记录为什么失败，后续无法构造有用 DPO 或错误分析。

处理：

```text
failure_type:
  invalid_action
  wrong_tool
  ignored_observation
  premature_final
  verifier_failed
  unsafe_action
  environment_error
```

### 6.4 数据过度依赖公开 Benchmark

公开 benchmark 可能被训练语料污染，也可能被社区反复优化。

处理：

- 公开 benchmark 只作参考。
- 建私有 held-out set。
- 定期新增新任务。
