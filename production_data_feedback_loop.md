# 生产数据回流流程

这份文档说明线上日志、用户反馈和失败案例如何进入训练数据。

## 1. 总流程

```text
线上日志
-> 隐私清洗
-> 失败分类
-> 人工/自动验证
-> 数据分流
-> SFT/DPO/RL/eval
-> 数据版本变更
-> 回归评估
```

线上数据不能直接进训练。

## 2. 哪些线上日志能用

可用：

- 用户明确授权的数据。
- 已脱敏工具轨迹。
- 失败类型和环境状态。
- 用户反馈。
- 公开网页/公开仓库任务。

不可用：

- 未授权隐私内容。
- secret、token、cookie。
- 内部客户数据原文。
- 法律限制不允许训练的数据。

## 3. 失败案例采样

不要只采样高频失败。还要采样：

- 高风险失败。
- 新类型失败。
- 高成本失败。
- 用户强负反馈。
- 安全边界失败。

采样字段：

```text
failure_type
task_type
model_version
tool_name
environment_version
severity
user_impact
```

## 4. 用户反馈如何变成 Preference

用户点赞/点踩不能直接等同 DPO 标签。

需要确认：

- 用户是否看到了完整结果。
- 点踩是因为错误、慢、贵、语气，还是任务没完成。
- 是否有环境 verifier。

处理：

```text
用户反馈 -> 候选 preference signal
verifier / 人工复核 -> DPO pair 或 RM data
```

## 5. 线上失败如何分流

```text
格式错误 -> SFT format data
工具选择错 -> DPO rejected / targeted SFT
未验证 final -> DPO pair
安全失败 -> safety negative / block metric
环境错误 -> infra issue，不进训练
新业务知识缺失 -> domain data
```

## 6. Regression Set

重大线上失败必须进入 regression set。

进入条件：

- 用户影响大。
- 安全风险。
- 高价值任务失败。
- 多次重复出现。
- 修复后必须长期防回归。

Regression set 不一定进入训练集。它首先是评估集。

## 7. 数据保留和退役

线上数据要有保留周期：

```text
raw logs: 短期保留
redacted trajectories: 中期保留
regression cases: 长期保留
training samples: 按数据版本管理
```

退役条件：

- 用户撤回授权。
- 工具协议过时。
- 数据被发现污染。
- 业务规则变化。

## 8. 回流发布门槛

一批线上回流数据进入训练前：

```text
secret_leak_count = 0
authorization_checked = true
failure_type_coverage recorded
manual_audit_pass_rate >= threshold
train_eval_overlap = 0
dataset_change_log written
```

