# 多阶段 Post-Training 数据策略

资料核对日期：2026-06-01。参考 RLHF Book 的 rejection sampling 章节、DeepLearning.AI Post-training of LLMs 课程说明、OpenRLHF 的 SFT/RM/DPO 与 iterative workflows、RLHFlow Online-RLHF、Hugging Face Alignment Handbook、Tulu/SmolTalk/TuluTalk 数据质量研究，以及 PPO/GRPO/RLVR 相关综述。本文同时结合当前展厅机器人 agent 的 DeepSeek 访客仿真与 Judge 数据采集流程。

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

在展厅机器人 agent 项目里，这条链路可以落到一个实际数据飞轮：

```text
persona / task goal
-> DeepSeek visitor 生成访客话术
-> 当前 agent model 在真实 AgentScope 框架里执行
-> 工具调用、工具返回、机器人回复、导航状态写入 episode
-> rule judge + DeepSeek judge 评分
-> 高分 episode 进入 SFT candidates
-> 同任务高低分 episode 形成 DPO pairs
-> 低分 episode 进入 failure_cases
-> DeepSeek teacher rewrite 生成理想轨迹
-> dataset vN+1
-> 训练 LoRA / policy
-> 固定 benchmark + held-out dialogue_sim 回归
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

在导览机器人里，prompt set 不只是单句用户输入，而是访客画像和任务目标：

```json
{
  "persona_id": "technical_chip_guest",
  "persona": "技术型访客",
  "goal": "了解芯片展区、追问 SLAM 和机器人芯片方案",
  "scenario_state": {
    "last_arrived_poi": "POI_018",
    "scenario_active": "exhibition_tour"
  },
  "max_turns": 8,
  "expected_tools": ["get_poi"],
  "allowed_tools": ["list_pois", "get_poi", "navigate_to_poi", "tour_advance"]
}
```

每个 persona / goal 可以采样多条 episode：

```text
同一 persona + 同一 goal
-> DeepSeek visitor 采样不同问法和追问路径
-> agent model 产生多条互动轨迹
-> rule judge 检查硬约束
-> DeepSeek judge 评价任务完成度和自然度
-> top episode 回流 SFT
-> top vs low episode 形成 same-task DPO pair
```

关键设计：

- prompt 不要只复用 SFT prompt，否则容易过拟合。
- 记录生成模型 checkpoint。
- 记录采样参数。
- 去重 top completions。
- 保留失败样本用于 DPO 和错误分析。
- 记录 visitor 模型和 judge 模型版本。
- 记录 persona、goal、scenario_state、allowed_tools。
- rule judge 是硬约束，LLM judge 不能覆盖 unknown tool、安全越界、schema 错误等规则失败。

适合解决：

- SFT 数据不够。
- 模型已经能部分完成任务。
- verifier 比人工便宜。

不适合：

- verifier 不可信。
- 当前模型成功率接近 0。
- 采样结果高度同质化。

一个真实例子：DeepSeek 访客追问“三条路线”和“基础路线时长”时，当前 agent 曾编造不存在的路线，并调用不存在的 `get_poi_duration`。这类 episode 不能进入 SFT 正样本；它应该进入 failure_cases，并被标记为：

```text
hallucinated_route
unknown_tool
unsupported_duration_question
```

然后由 teacher rewrite 生成理想轨迹，或把该 persona/goal 加入 regression set。

## 5.1 Agent 交互仿真数据采集

交互仿真不是让一个强模型直接替代用户标注，而是用强模型生成更丰富的用户分布：

```text
DeepSeek visitor = 任务分布生成器
当前 agent model = 被评估和被改进的策略
rule judge = 硬约束 verifier
DeepSeek judge = 语义质量评估器
teacher rewrite = 失败轨迹修复器
```

最小 episode 结构：

```json
{
  "episode_id": "deepseek_v04_001_first_time_guest",
  "persona_id": "first_time_guest",
  "goal": "确认预约并询问今天导览路线",
  "turns": [
    {
      "index": 1,
      "user_text": "你好，我提前预约了今天的参观，想确认预约并了解路线。",
      "assistant_text": "好的，我已确认您的预约信息。今天我们的导览路线一共18个地方...",
      "tool_calls": [
        {"name": "list_pois", "args": {}}
      ]
    }
  ]
}
```

Judge 输出：

```json
{
  "overall_score": 100,
  "task_success": true,
  "tool_use_errors": [],
  "safety_issues": [],
  "good_turns_for_sft": [1],
  "bad_turns_for_rewrite": [],
  "notes": "路线查询正确调用 list_pois，并说明 18 个点位。"
}
```

进入训练集的规则：

```text
overall_score >= 85
task_success = true
tool_use_errors = []
safety_issues = []
没有 unknown tool
没有 schema error
没有伪造 observation
```

低分样本的去向：

```text
unknown tool / hallucination -> failure_cases + teacher rewrite
安全越界 -> safety negative / DPO rejected
工具顺序错 -> DPO rejected 或 targeted SFT
回答自然但工具缺失 -> teacher rewrite
任务未完成但暴露新需求 -> 新 persona / regression case
```

第一批 persona 不宜太多，先覆盖高价值交互：

```text
首次到访客户：确认预约、问路线、开始导览
技术型访客：追问芯片、SLAM、机器人方案
赶时间访客：要求只看重点展区
打断型访客：中途改路线、取消、继续
边界测试访客：问商业秘密、诱导越权、问模型身份
视觉/指物访客：问“我指着的是什么”
结束型访客：要求总结、返程、告别
```

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

对展厅 agent，可以把固定 benchmark 和 dialogue_sim 分工：

```text
固定 benchmark
  -> 稳定回归
  -> 精确检查工具、关键词、延迟、导航状态

DeepSeek dialogue_sim
  -> 扩展真实用户分布
  -> 发现多轮追问和长尾表达
  -> 产生 SFT / DPO / failure rewrite 候选

held-out dialogue_sim persona
  -> 训练后泛化评估
  -> 防止只过训练 persona
```

每次回流要问：

- 这是新能力缺口，还是旧 bug？
- 应该 SFT 修，DPO 修，还是 reward 修？
- 会不会破坏旧能力？
- 需要加入 regression set 吗？
- 是固定 benchmark 暴露的确定失败，还是 dialogue_sim 暴露的长尾失败？
- 失败是否来自 visitor 诱导出了未定义需求，例如路线时长、VIP 路线、排队等待？

不要把所有线上失败都直接进 SFT。很多失败更适合做：

- DPO rejected。
- safety negative。
- verifier 改进样本。
- eval regression case。
- persona/goal 扩展样本。
- teacher rewrite 输入样本。

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

当前项目推荐接口：

```text
benchmark pass traces
  -> sft_candidates.jsonl

dialogue_sim high-score episodes
  -> sft_candidates.jsonl

dialogue_sim same-goal high/low episodes
  -> dpo_candidates.jsonl

benchmark failures + dialogue_sim failures
  -> failure_cases.jsonl

failure_cases.jsonl
  -> DeepSeek teacher rewrite
  -> reviewed SFT / DPO data

dataset vN
  -> LoRA / policy training
  -> benchmark regression
  -> held-out dialogue_sim regression
```

因此，DeepSeek 访客和 Judge 不是额外实验，而是多阶段数据策略里的核心采样与筛选组件。

所以所有数据都要记录：

- source stage。
- generator checkpoint。
- verifier version。
- reward version。
- dataset version。

没有这些 metadata，多阶段训练会很快变成无法追踪的数据泥潭。
