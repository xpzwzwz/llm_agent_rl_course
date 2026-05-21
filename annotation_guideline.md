# 标注员操作指南

这份文档用于组织 SFT、DPO、Reward Model 和 agent trajectory 标注。

## 1. 标注目标

标注不是判断“哪个回答更像人”，而是判断：

```text
哪条回答或轨迹更正确、更安全、更遵循任务、更经过验证
```

优先级：

1. 安全性。
2. 任务正确性。
3. 是否经过验证。
4. 是否遵循工具和格式。
5. 完整性。
6. 简洁性和表达。

不要因为回答更长、更礼貌、更像报告就判好。

## 2. 标注界面应该展示什么

最少展示：

- 用户任务。
- system/tool 约束。
- 两条候选轨迹。
- 每步 action。
- 每步 tool result。
- verifier 结果。
- 成本和步骤数。
- 已知安全标签。

不要展示：

- hidden answer。
- hidden tests 结果，除非标注任务明确要求专家复审。
- 可能诱导偏好的模型名称。

## 3. DPO Pair 标注规则

优先选：

```text
完成任务 > 未完成
安全 > 不安全
验证成功 > 未验证
正确工具链 > 猜测 final
少量有效步骤 > 大量重复步骤
官方来源 > 不可信来源
```

如果两条都失败：

- 选择更接近成功的一条。
- 如果无法判断，标为 tie / needs_review。

如果一条更长：

- 不因长度加分。
- 只看是否提供了必要信息和验证。

## 4. Reward Model 标注规则

标注 pair 时记录 reason：

```text
chosen 更好，因为它运行了测试并通过；rejected 直接给建议，没有验证。
```

reason 应具体，不要写：

```text
chosen 更好。
```

## 5. 什么时候升级专家

必须升级：

- 安全或隐私风险。
- 法律、医疗、金融高风险。
- 两条候选都部分正确。
- verifier 和人工判断冲突。
- 工具结果看不懂。
- 需要业务知识判断。

## 6. Gold Questions

每批标注混入 gold questions：

- 明显成功 vs 明显失败。
- 安全拒绝 vs 越权执行。
- verified trajectory vs unverified final。
- 短正确 vs 长错误。

标注员 gold accuracy 低于阈值时：

- 暂停该批标注。
- 复训标注员。
- 复审其最近标注。

## 7. 标注一致性

每批记录：

```text
num_items
num_annotators
agreement_rate
conflict_rate
adjudication_rate
gold_accuracy
```

冲突样本处理：

- 第三人复审。
- 专家仲裁。
- 或从训练集中剔除。

## 8. 标注输出格式

```json
{
  "task_id": "github_fix_001",
  "chosen_id": "run_a",
  "rejected_id": "run_b",
  "label": "chosen_a",
  "confidence": "high",
  "reason": "A 运行测试并通过，B 没有验证。",
  "annotator_id": "ann_001",
  "needs_review": false
}
```

必须保留 `reason` 和 `confidence`。

