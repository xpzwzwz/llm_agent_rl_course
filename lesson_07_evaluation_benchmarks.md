# 第七课：评估基准和自建 Benchmark

## 1. 为什么评估比训练更先重要

Agent 训练很容易出现错觉：训练 reward 上升，但真实任务没有变强。

原因包括：

- reward 被模型钻空子。
- 训练集和评估集泄漏。
- LLM judge 偏好长回答。
- 工具环境太简单。
- 成功标准不明确。

所以在做 RL 前，应该先建立固定评估集。

## 2. 常见基准

ToolBench 关注工具调用和 API 使用。适合评估模型能否选择工具、生成参数、组合 API。

WebArena 关注真实网页环境。适合评估浏览器操作、页面理解和多步任务完成。

SWE-bench 关注真实 GitHub issue 修复。适合评估 coding agent 是否能生成通过测试的 patch。

AgentGym 关注跨环境 agent 训练和评估。它的方向是让 agent 在多种环境中学习和演化。

这些基准覆盖不同能力，不应该只看一个分数。

## 3. 评估指标

建议同时记录：

- `success_rate`：任务最终成功率。
- `pass_at_k`：采样 k 次是否至少一次成功。
- `avg_steps`：平均动作数。
- `invalid_action_rate`：非法工具调用比例。
- `recovery_rate`：失败后恢复比例。
- `cost`：token、API、时间成本。
- `safety_violation_rate`：越权、危险动作比例。

对 coding agent，还要记录：

- 测试通过率。
- patch 大小。
- 修改文件数量。
- 是否新增或修改测试。
- hidden tests 通过率。

## 4. 自建 Benchmark

业务场景通常需要自建 benchmark。步骤：

1. 选 50 到 200 个真实任务。
2. 每个任务写清楚初始状态和成功标准。
3. 把环境固定到可复现版本。
4. 给每个任务写自动验证器。
5. 定期跑同一批任务。
6. 保存完整 trajectory，方便回放和诊断。

成功标准要尽量机器可判定。例如：

```text
数据库字段变成 expected value
页面出现 expected text
pytest 指定测试通过
API 返回 expected JSON
```

## 5. 错误分析

评估后要分类失败原因：

- 没理解任务。
- 选错工具。
- 参数错误。
- 没读懂 observation。
- 中途计划错误。
- 已经成功但继续操作导致失败。
- 没有验证。
- 环境或工具本身不稳定。

错误分类会直接决定下一步训练：

- 格式错误多：补 SFT。
- 好坏策略分不清：补 DPO。
- 探索不足：做多采样和 RL。
- 环境反馈不清楚：改工具返回值和 reward。

