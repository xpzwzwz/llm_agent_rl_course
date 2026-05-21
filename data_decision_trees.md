# 数据决策树

这份文档把常见数据处理问题写成决策树，方便快速判断一条样本应该去哪。

## 1. 一条 Trajectory 怎么处理

```text
是否包含 secret / PII / 越权动作？
  是 -> Reject 或脱敏后作为安全负样本
  否 -> 继续

是否可解析 action？
  否 -> invalid action 统计；可做 rejected，不进 SFT
  是 -> 继续

是否最终 verifier 成功？
  是 -> 继续
  否 -> 看是否有恢复过程

是否失败后成功恢复？
  是 -> 可进 SFT，标 recovery
  否 -> DPO rejected / 错误分析

是否有重复无效动作？
  是 -> 降级为 B/C，或清洗后再用
  否 -> A/B 级候选
```

## 2. 失败样本怎么用

```text
失败类型是什么？

invalid_action
  -> 格式数据补强；可做 DPO rejected

wrong_tool / bad_arguments
  -> 工具选择负样本；可做 DPO rejected

ignored_observation
  -> 多步恢复数据补强；可做 DPO rejected

premature_final
  -> 构造“verified trajectory > unverified final” pair

unsafe_action
  -> safety negative；不进普通 SFT

environment_error
  -> 不进训练；修环境或工具

reward_hacking
  -> 修 sandbox/reward；作为 negative 样本
```

## 3. 一条 Pair 是否能进 DPO

```text
prompt 是否相同？
  否 -> Reject
  是 -> 继续

chosen 是否明显优于 rejected？
  否 -> 降权或复审
  是 -> 继续

偏好来源是什么？
  verifier -> 高可信
  human -> 高可信但看一致性
  multi-judge -> 中可信
  single judge -> 低可信，需抽查
  rule -> 看规则是否可靠

chosen/rejected 是否被截断？
  是 -> 抽查关键差异是否保留
  否 -> 继续

chosen 是否只是更长？
  是 -> 复审或 Reject
  否 -> 可入 DPO
```

## 4. 一批 Synthetic Data 怎么处理

```text
是否有 verifier？
  否 -> 低权重，只做候选
  是 -> 继续

是否模板重复严重？
  是 -> 去重 / 降权
  否 -> 继续

是否覆盖真实错误和恢复？
  否 -> 不能替代真实轨迹
  是 -> 继续

是否人工抽查通过？
  否 -> 暂停使用
  是 -> 可进入 active 数据池
```

## 5. 新数据应该进哪个阶段

```text
数据主要教格式？
  -> format warmup / SFT

数据是高质量成功轨迹？
  -> Agent SFT

数据是一好一坏对比？
  -> DPO / Reward Model

数据来自当前模型多采样？
  -> rejection sampling / DPO / SFT 回流

数据只有 prompt 和环境？
  -> GRPO/PPO prompt set

数据是线上失败案例？
  -> failure analysis -> 决定 SFT/DPO/RL/eval
```

