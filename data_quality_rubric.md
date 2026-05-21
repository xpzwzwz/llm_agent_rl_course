# 数据质量 Rubric

资料核对日期：2026-05-21。本页用于数据验收。它把样本分成 A/B/C/Reject 四档。

## 1. 总体等级

| 等级 | 用途 | 标准 |
|---|---|---|
| A | 可进主训练集 | verified success，格式正确，来源清楚，无隐私风险 |
| B | 可进训练集但低权重 | 基本正确，有轻微冗余或摘要损失 |
| C | 只用于分析或 rejected | 有明显缺陷，但能表达失败模式 |
| Reject | 丢弃 | 隐私泄露、伪造 observation、越权动作、无法解析 |

## 2. SFT Rubric

A 级：

- 轨迹最终成功。
- action 格式稳定。
- tool result 来自真实环境。
- final 前有必要验证。
- 无重复无效动作。
- 无 secret。

B 级：

- 成功但步骤略冗余。
- tool result 被摘要但保留关键信息。
- final 表述一般但任务完成。

C 级：

- 部分成功。
- 有错误但最终恢复不完整。
- 可作为失败恢复研究样本。

Reject：

- 最终失败还当成完成。
- 模型伪造 observation。
- 删除测试或绕过验证。
- 泄露 secret。

## 3. DPO Rubric

A 级：

- chosen/rejected 同 prompt。
- chosen verifier 成功，rejected 失败。
- reward gap 明显。
- chosen 不只是更长，而是更正确。
- preference reason 清楚。

B 级：

- chosen 明显更好，但没有 deterministic verifier。
- 多 judge 一致。
- 有人工复核。

C 级：

- 差异小。
- rejected 太弱。
- 只能做低权重 pair。

Reject：

- prompt 不一致。
- chosen/rejected 被截断后无法比较。
- 标签和 verifier 冲突且未解释。
- chosen 只是格式更好但内容错误。

## 4. Reward Model Rubric

A 级：

- 标注指南明确。
- 标注员一致性高。
- 覆盖 hard negative。
- train/eval 按 prompt split。

B 级：

- 有轻微标注冲突但已复审。
- 部分样本来自 judge，但有抽查。

C 级：

- 标签来源不稳定。
- 只能用于初筛或弱监督。

Reject：

- chosen 总是同一模型生成。
- rejected 总是明显乱码。
- eval prompt 泄漏到 train。

## 5. Agent Trajectory Rubric

A 级：

- raw log 完整。
- trajectory 可回放。
- provenance 清楚。
- verifier 可信。
- model-visible 和 verifier-only 字段隔离。

B 级：

- 可回放性部分缺失，但工具结果可信。
- 摘要有 raw_ref。

C 级：

- 失败轨迹，有明确 failure_type。
- 可用于 DPO rejected 或错误分析。

Reject：

- 环境状态不可解释。
- 工具结果无法确认来源。
- hidden answer 泄漏到 observation。
- 安全边界被突破。

## 6. 批次验收门槛

一批数据进入正式训练前：

```text
secret_leak_count = 0
train_eval_task_overlap = 0
invalid_json_rate < 1%
unknown_tool_rate < 0.5%
verified_success_rate >= 80% for SFT
chosen_rejected_reward_gap_avg >= 0.5 for DPO
truncated_pair_rate < 5%
manual_audit_pass_rate >= 95%
```

不达标处理：

- 安全问题：整批暂停。
- split 泄漏：重新 split。
- 格式问题：修转换脚本。
- 质量问题：降权或重采。

## 7. 抽检比例

建议：

```text
小于 1k 样本：抽检 5%
1k 到 100k：抽检 1%，不少于 100 条
大于 100k：抽检 0.2%，不少于 1000 条
高风险任务：额外抽检 5%
```

高风险包括代码修改、网页表单、API 写操作、隐私数据、金融/医疗/法律场景。

