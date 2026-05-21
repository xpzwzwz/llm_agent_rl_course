# 数据问题排查索引

这份文档面向“已经遇到问题”的数据构造者。先按症状定位，再去对应文档细查。

## 1. SFT 后不会调用工具

先查：

- 工具调用样本比例是否太低。
- action 格式是否混乱。
- chat template 是否正确表达 tool role。
- assistant-only loss 是否只算 assistant。

去看：

- [SFT 数据构造手册](sft_data_construction_guide.md)
- [工具调用格式怎么选](lesson_10_tool_calling_formats.md)
- [数据 Schema 参考](data_schema_reference.md)

## 2. SFT 后模型伪造 Observation

高概率原因：

- tool message 被算进 loss。
- 日志转换时把 observation 放到了 assistant role。
- 训练样本里出现 assistant 自己写 `Observation`。

处理：

- 抽查 token label。
- 修 chat template。
- 把这类样本从 SFT 移除。

去看：

- [SFT 数据构造手册](sft_data_construction_guide.md)
- [坏数据案例库](bad_data_examples.md)

## 3. DPO 后模型变短、不行动

高概率原因：

- chosen 多是短 final。
- rejected 是长但失败的工具轨迹。
- pair 无意中奖励“少做少错”。

处理：

- 构造“已验证 trajectory > 未验证 final”的 pair。
- 统计 chosen/rejected action 数。
- 统计 chosen/rejected 长度分布。

去看：

- [Preference / DPO 数据构造手册](preference_data_construction_guide.md)
- [训练过程问题清单](training_process_failure_modes.md)

## 4. Chosen 总是比 Rejected 长

风险：

- DPO 学到 length bias。
- judge 偏好长回答。
- 模型训练后成本上升。

处理：

- 加入“短但正确 > 长但错”pair。
- 记录 length ratio。
- judge rubric 明确不因长度加分。

去看：

- [Preference / DPO 数据构造手册](preference_data_construction_guide.md)
- [评估和 LLM Judge 问题清单](evaluation_and_judge_failure_modes.md)

## 5. GRPO Reward 上升但 Eval 不升

高概率原因：

- reward function 被钻空子。
- process reward 权重太高。
- eval 和 train prompt 泄漏或分布不同。
- verifier 不可信。

处理：

- 抽查高 reward 失败轨迹。
- 加 hidden verifier。
- 降低过程奖励。
- 检查 task_id overlap。

去看：

- [训练过程问题清单](training_process_failure_modes.md)
- [评估和 LLM Judge 问题清单](evaluation_and_judge_failure_modes.md)
- [Agent 安全和工具边界问题清单](agent_security_and_tool_failure_modes.md)

## 6. 同一批数据训练效果忽好忽坏

高概率原因：

- 数据混比不稳定。
- synthetic data 比例过高。
- train/eval split 不稳定。
- 数据版本缺少变更记录。

处理：

- 固定数据版本。
- 写 change log。
- 每次只改一个主要变量。

去看：

- [数据混比和 Curriculum 设计](data_mixture_and_curriculum.md)
- [数据版本变更模板](dataset_change_log_template.md)

## 7. 评估分数高，但人工看很差

高概率原因：

- LLM judge 偏好格式/长度。
- eval set contamination。
- metric gaming。
- verifier 太弱。

处理：

- 加人工抽查。
- 加 position swap judge。
- 增加 hidden checks。

去看：

- [评估和 LLM Judge 问题清单](evaluation_and_judge_failure_modes.md)

## 8. 失败轨迹不知道该怎么用

快速判断：

```text
失败后恢复 -> SFT
失败且未恢复 -> DPO rejected
安全失败 -> safety negative
环境错误 -> 不进训练，进 infra bug
reward hacking -> negative / sandbox 修复
```

去看：

- [数据决策树](data_decision_trees.md)
- [Agent Trajectory 数据构造手册](agent_trajectory_data_guide.md)

