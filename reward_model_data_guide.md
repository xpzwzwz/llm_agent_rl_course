# Reward Model 数据构造手册

资料核对日期：2026-05-21。参考 RLHF Book、OpenRLHF reward model 文档、Secrets of RLHF Part II、Preference Proxy Evaluations 和 reward generalization 相关研究。

## 1. Reward Model 数据和 DPO 数据的区别

DPO 直接用 pair 更新 policy。

Reward Model 数据用于训练：

```text
r_phi(prompt, response_or_trajectory) -> scalar reward
```

然后 PPO/GRPO 或 rejection sampling 使用这个分数。

同样是 preference pair，但 reward model 更关心泛化：它要给没见过的新输出打分。

## 2. Pairwise 还是 Scalar Rating

Pairwise：

```text
chosen > rejected
```

优点：

- 标注员更容易比较。
- 噪声通常低于绝对打分。
- 适合训练 Bradley-Terry 风格 RM。

Scalar rating：

```text
response score = 1..5
```

优点：

- 可以表达绝对质量。
- 适合多维 rubric。

缺点：

- 不同标注员尺度不一致。
- 需要校准。

起步建议 pairwise。

## 3. 标注指南

标注指南必须写清优先级：

```text
1. 正确性
2. 安全性
3. 遵循指令
4. 完整性
5. 简洁性
6. 风格
```

对 agent 轨迹，还要写：

```text
已验证完成 > 未验证但看似合理
安全拒绝 > 危险执行
官方来源 > 不可信网页
少量有效步骤 > 大量重复步骤
```

每个 pair 最好记录 `preference_reason`。

## 4. 标注一致性

记录：

```text
inter_annotator_agreement
conflict_rate
adjudication_rate
gold_task_accuracy
```

对冲突样本：

- 进入复审。
- 或者从训练集中剔除。
- 或者降低权重。

不要把冲突样本直接当高质量偏好数据。

## 5. Reward Model Train/Eval Split

必须按 prompt/task split。

错误：

```text
同一 prompt 的 pair 一部分进 train，一部分进 eval
```

正确：

```text
train prompts 和 eval prompts 不重叠
```

对 agent：

- 按 `task_id` split。
- 按环境版本 split。
- 对相似 issue / 相似网页任务去重。

## 6. 分布覆盖

Reward model 要覆盖：

- 短回答和长回答。
- 单轮和多轮。
- 工具调用和非工具调用。
- 成功、部分成功、失败。
- 安全拒绝和危险执行。
- 高质量 hard negative。

如果 reward model 没见过 agent 轨迹，却拿去给 agent RL 打分，风险很高。

## 7. Reward Model 评估

不要只看 pairwise accuracy。

至少看：

```text
pairwise_accuracy
calibration
length_bias
domain_breakdown
hard_negative_accuracy
verifiable_task_correlation
human_eval_correlation
```

如果 RM 分数和 verifier 成功率不相关，就不该用于 RL。

## 8. RM 数据常见污染

- chosen 总是更长。
- rejected 总是格式更差。
- 某个生成模型只出现在 chosen。
- 标注员偏好某种语气。
- 安全和有用性标准冲突未标明。
- eval pair 来自 train prompt。

处理：

- 记录 generator model。
- 记录长度分布。
- 按 domain 分桶。
- 加 adversarial rejected。
- 做 held-out domain eval。

