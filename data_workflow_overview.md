# 数据构造工作流总览

这份文档给新成员一张总图，说明数据从哪里来、经过哪些处理、最后进入哪些训练阶段。

## 1. 总流程

```text
raw logs / public datasets / human demos / synthetic data
  -> redaction
  -> normalization
  -> replay / verifier
  -> trajectory dataset
  -> quality audit
  -> split by task_id
  -> SFT builder
  -> DPO pair builder
  -> RM pair builder
  -> RL prompt builder
  -> dataset card + change log
  -> training
  -> evaluation
  -> failure analysis
  -> feedback loop
```

## 2. 每一步产物

| 步骤 | 输入 | 输出 | 负责人 |
|---|---|---|---|
| redaction | raw log | 脱敏 raw log | 数据工程 / 安全 |
| normalization | 多源日志 | 标准 trajectory | 数据工程 |
| replay / verifier | trajectory | success/failure 标签 | 评估 / 工程 |
| quality audit | 标准数据 | A/B/C/Reject | 数据负责人 |
| split | task 数据 | train/eval/test | 数据工程 |
| SFT builder | 成功轨迹 | SFT JSONL | 数据工程 |
| DPO builder | 多轨迹/偏好 | DPO JSONL | 标注 / 数据 |
| RL prompt builder | 任务+环境 | RL prompt set | 训练工程 |
| change log | 数据版本 | 变更记录 | 项目负责人 |

## 3. 三条主线

SFT 主线：

```text
成功/恢复 trajectory -> SFT JSONL -> format/behavior model
```

DPO 主线：

```text
same-task 多条 trajectory -> chosen/rejected -> preference model
```

RL 主线：

```text
prompt + environment + verifier -> rollout -> reward -> policy update
```

## 4. 不同阶段的关口

进入 SFT 前：

- secret 清零。
- trajectory 成功或恢复。
- assistant/tool role 正确。

进入 DPO 前：

- prompt 相同。
- chosen/rejected 可比。
- reward gap 或人工理由明确。

进入 RL 前：

- environment 可重置。
- verifier 可信。
- prompt 与 eval 隔离。

进入 eval 前：

- task_id 不和 train 重叠。
- hidden checks 不泄漏。
- 评估版本固定。

