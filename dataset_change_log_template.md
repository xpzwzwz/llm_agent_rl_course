# 数据版本变更模板

每次数据版本变化都应该写 change log。数据变更要像代码变更一样可追踪、可回滚。

## 1. 模板

```yaml
dataset_name: agent_posttrain_mix
version: v4.2
date: 2026-05-21
owner: data-team

base_version: v4.1

summary:
  - 增加 browser recovery trajectories
  - 降低 synthetic DPO pair 权重
  - 删除旧 XML action format 数据

added:
  - name: browser_recovery_v2
    samples: 3200
    reason: browser eval premature_final_rate 高

removed:
  - name: xml_tool_format_v1
    samples: 1800
    reason: 工具协议已迁移到 JSON action

downweighted:
  - name: synthetic_general_dpo_v1
    old_weight: 0.25
    new_weight: 0.10
    reason: 人工抽查发现模板化严重

mixture:
  format: 0.10
  browser: 0.25
  coding: 0.30
  api: 0.15
  safety: 0.10
  general: 0.10

quality_checks:
  secret_leak_count: 0
  train_eval_task_overlap: 0
  invalid_action_rate: 0.006
  truncated_pair_rate: 0.032
  manual_audit_pass_rate: 0.97

expected_effect:
  - browser success rate 提升
  - premature_final_rate 下降

risks:
  - browser 权重提高可能影响 coding
  - recovery 数据过多可能增加 avg_steps

required_eval:
  - browser_heldout_v2
  - coding_regression_v1
  - safety_prompt_injection_v1
  - general_chat_v1

rollback_condition:
  - coding success rate 下降超过 3%
  - avg_steps 上升超过 20%
  - safety violation rate 上升
```

## 2. 变更说明应该回答什么

- 为什么改？
- 加了什么？
- 删了什么？
- 降权了什么？
- 预期提升什么？
- 可能破坏什么？
- 哪些评估必须跑？
- 什么条件下回滚？

## 3. 不合格变更记录

坏例子：

```text
加了一些新数据，效果应该会更好。
```

问题：

- 没有版本。
- 没有样本数。
- 没有来源。
- 没有风险。
- 没有必跑评估。
- 不能回滚。

数据版本不可追踪时，训练结果也不可解释。

