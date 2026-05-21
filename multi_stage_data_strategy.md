# 多阶段 Post-Training 数据策略

资料核对日期：2026-05-21。参考 RLHF Book 的 rejection sampling 章节、DeepLearning.AI Post-training of LLMs 课程说明、OpenRLHF 的 SFT/RM/DPO 与 iterative workflows、RLHFlow Online-RLHF、Hugging Face Alignment Handbook、Tulu/SmolTalk/TuluTalk 数据质量研究，以及 PPO/GRPO/RLVR 相关综述。

## 1. 核心问题

数据构造不是一次性工作，而是多阶段系统：

```text
format warmup
-> agent SFT
-> preference / DPO
-> rejection sampling
-> GRPO/PPO online RL
-> continual data flywheel
```

每一阶段需要的数据不同，目标也不同。把所有数据混在一起训练，通常会导致：

- 工具格式学不稳。
- DPO 学到风格而不是任务能力。
- RL reward 上升但真实成功率不升。
- 新能力提升但旧能力遗忘。

## 2. 阶段 0：Format Warmup

目标：让模型稳定遵守协议。

数据：

- 单步工具调用。
- JSON/XML/tool-call 格式。
- schema 参数填充。
- 安全拒绝。
- 不调用工具的普通问答。

样本特点：

```text
短
格式清楚
任务简单
覆盖所有工具
```

不应该放：

- 复杂长程任务。
- 噪声很大的网页轨迹。
- 未清洗失败轨迹。

验收指标：

```text
invalid_action_rate < 1%
unknown_tool_rate < 0.5%
schema_error_rate < 1%
```

## 3. 阶段 1：Agent SFT

目标：让模型学会完整行动链。

数据：

- 成功 trajectory。
- 失败后恢复 trajectory。
- browser/coding/API 分场景轨迹。
- 先验证再 final 的轨迹。

数据来源：

- 人类专家示范。
- 强模型生成后人工/ verifier 筛选。
- OpenHands/browser-use/LangGraph 运行日志。

关键原则：

- SFT 只模仿“应该做什么”。
- 不要模仿未恢复失败。
- 工具返回必须来自环境。

典型混比：

```text
format/tool single-step: 10%
agent success trajectories: 55%
recovery trajectories: 15%
ordinary instruction data: 15%
safety/refusal data: 5%
```

## 4. 阶段 2：Preference / DPO

目标：让模型偏好更好的策略。

数据：

- 同一 task 多条 trajectory。
- success vs failure。
- verified vs unverified。
- hard negative。
- safe refusal vs unsafe execution。

关键是 same-task comparison：

```text
同一任务下比较两条路径
```

不要拿不同任务的回答配 pair。

DPO 阶段应该重点惩罚：

- 提前 final。
- 不验证。
- 重复工具调用。
- 伪造 observation。
- 越权动作。

## 5. 阶段 3：Rejection Sampling

RLHF Book 把 rejection sampling 描述为一种常见、简单的 preference fine-tuning baseline：用当前模型对 prompt 采样多个 completion，用 reward model 或 verifier 筛选，再对 top completions 做 SFT。

Agent 版流程：

```text
选 prompt set
-> 当前模型每个 prompt 采样 N 条 trajectory
-> verifier / reward model 打分
-> top trajectory 回流 SFT
-> success/failure 组成 DPO pair
```

关键设计：

- prompt 不要只复用 SFT prompt，否则容易过拟合。
- 记录生成模型 checkpoint。
- 记录采样参数。
- 去重 top completions。
- 保留失败样本用于 DPO 和错误分析。

适合解决：

- SFT 数据不够。
- 模型已经能部分完成任务。
- verifier 比人工便宜。

不适合：

- verifier 不可信。
- 当前模型成功率接近 0。
- 采样结果高度同质化。

## 6. 阶段 4：GRPO / PPO Online RL

目标：让模型通过环境反馈探索超出离线数据的策略。

数据不再是完整答案，而是 prompt/environment：

```json
{
  "task_id": "github_fix_001",
  "prompt": "修复这个 issue。",
  "environment": "docker://repo_v1",
  "tools": ["read_file", "edit_file", "run_tests"],
  "verifier": "hidden_tests_v1",
  "max_steps": 30
}
```

Prompt set 设计：

- 难度分桶。
- 场景分桶。
- 成功率分桶。
- 安全风险分桶。
- held-out eval 隔离。

GRPO 特别需要注意：

- 每个 prompt 多条采样。
- 组内 reward 不能全相同。
- reward std 接近 0 的任务要移出或改 reward。

PPO 特别需要注意：

- reward model 覆盖 agent 轨迹。
- value model 稳定。
- KL 和 entropy 监控。

## 7. 阶段 5：Continual Data Flywheel

上线或大规模评估后，数据会滚动演化：

```text
新失败案例
-> failure classification
-> targeted data generation
-> SFT/DPO/RL update
-> regression eval
-> dataset version update
```

每次回流要问：

- 这是新能力缺口，还是旧 bug？
- 应该 SFT 修，DPO 修，还是 reward 修？
- 会不会破坏旧能力？
- 需要加入 regression set 吗？

不要把所有线上失败都直接进 SFT。很多失败更适合做：

- DPO rejected。
- safety negative。
- verifier 改进样本。
- eval regression case。

## 8. 数据生命周期

数据不是永久等权。

状态：

```text
candidate
approved
active
downweighted
retired
regression_only
```

需要退役的数据：

- 工具协议旧版本。
- 环境已废弃。
- 标注标准过时。
- 被发现有泄漏。
- 被新数据覆盖且质量更低。

需要长期保留的数据：

- 安全边界样本。
- 关键格式样本。
- 历史 regression case。
- 高质量专家示范。

## 9. 阶段间接口

每阶段输出要能服务下一阶段：

```text
SFT output -> initial policy
DPO output -> better policy
RS output -> new SFT + new DPO
GRPO/PPO rollout -> failure analysis + new prompt set
Eval failures -> regression + targeted data
```

所以所有数据都要记录：

- source stage。
- generator checkpoint。
- verifier version。
- reward version。
- dataset version。

没有这些 metadata，多阶段训练会很快变成无法追踪的数据泥潭。

