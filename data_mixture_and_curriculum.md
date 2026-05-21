# 数据混比和 Curriculum 设计

资料核对日期：2026-05-21。参考 Alignment Handbook 的 dataset mixer 思路、RLHF Book、OpenRLHF 数据管线、Tulu/SmolTalk/TuluTalk 数据质量研究、forgetting 相关 SFT/DPO 研究，以及 post-training data mixture 讨论。

## 1. 为什么混比重要

同样的数据，不同混比会训练出不同模型。

常见失败：

- agent 数据太多，普通聊天变差。
- 安全拒绝太多，模型过度拒绝。
- coding 数据太多，网页任务退化。
- 简单格式数据太少，RL 后格式崩。
- 新任务数据太多，旧能力遗忘。

数据混比是 post-training 的核心超参之一。

## 2. 基础混比模板

Agent SFT 起步模板：

```text
format/tool schema: 10%
agent success trajectories: 45%
recovery trajectories: 15%
ordinary instruction following: 15%
safety/refusal: 10%
domain-specific knowledge: 5%
```

DPO 起步模板：

```text
verified success vs failure: 45%
verified trajectory vs unverified final: 20%
hard negative: 20%
safety pair: 10%
cost/length preference: 5%
```

GRPO/PPO prompt 起步模板：

```text
easy tasks: 20%
medium tasks: 50%
hard tasks: 20%
safety/adversarial tasks: 10%
```

这些不是定律，只是起点。真实比例要根据评估调整。

## 3. 难度 Curriculum

不要一开始用最难任务做 RL。

推荐：

```text
single-step tool
-> 2-3 step tool chain
-> short browser/coding tasks
-> failure recovery tasks
-> long-horizon tasks
-> adversarial/safety tasks
```

每一阶段晋级条件：

```text
success_rate >= threshold
invalid_action_rate <= threshold
avg_steps stable
no major safety regression
```

如果模型在简单任务上格式都不稳，直接上长程 RL 只会制造噪声 rollout。

## 4. 场景混比

Agent 常见场景：

- tool/API。
- browser。
- coding。
- data analysis。
- safety。

每个场景单独评估，不要只看总分。

如果 coding 提升、browser 下降，要调整场景权重，而不是继续加总数据。

建议报告：

```text
scenario   train_weight   eval_success   regression
tool       0.25           0.72           +0.05
browser    0.20           0.41           -0.08
coding     0.35           0.55           +0.12
safety     0.10           0.93           +0.01
general    0.10           0.80           -0.02
```

## 5. 旧数据保留和遗忘

多阶段训练会遗忘旧能力。

缓解：

- 保留一部分高质量 SFT 数据。
- DPO/RL 后继续跑普通能力 eval。
- 使用 replay buffer。
- 关键格式和安全样本长期保留。
- 对旧场景 regression case 加权。

不要每阶段都只用最新数据。

## 6. On-policy 和 Off-policy 数据

SFT/DPO 多数是 offline：

```text
固定数据集
```

Rejection sampling / RL 是 on-policy 或 semi-online：

```text
当前模型生成新样本
```

区别：

- off-policy 稳定，但可能不覆盖当前模型错误。
- on-policy 贴近当前模型，但成本高、容易反馈循环。

数据池要记录：

```text
generated_by_checkpoint
policy_version
sampling_temperature
num_generations
verifier_version
```

否则无法判断某批数据是否仍然适合当前模型。

## 7. Synthetic Data 混比

合成数据有用，但不能失控。

风险：

- 模板化。
- 过度理想。
- judge/style leakage。
- 错误被放大。
- 缺少真实失败恢复。

建议：

```text
synthetic <= 50% for early experiments
synthetic high-quality verified can be higher
unverified synthetic should be low weight
```

所有 synthetic 数据记录：

- generator model。
- prompt template。
- verification result。
- human audit rate。

## 8. 数据权重和采样

不是所有数据等权。

可按质量和用途加权：

```text
A-grade expert trajectory: high
verified model trajectory: medium
synthetic unverified: low
failure rejected: DPO only
safety critical: high but capped
```

注意 safety 数据不能无限加权，否则模型可能过度拒绝。

## 9. 混比实验

每次只改一个主要变量：

```text
browser 20% -> 30%
hard negative 10% -> 20%
recovery trajectory 5% -> 15%
synthetic 50% -> 30%
```

记录：

- 数据版本。
- 混比表。
- 训练参数。
- 场景分桶评估。
- regression。

不要同时换数据、模型、reward、学习率，否则无法归因。

## 10. 推荐数据版本记录

```yaml
dataset_version: agent_mix_v4
base: agent_mix_v3
changes:
  - browser tasks from 15% to 25%
  - added 3k recovery trajectories
  - removed old XML action format data
mixture:
  format: 0.10
  browser: 0.25
  coding: 0.30
  api: 0.15
  safety: 0.10
  general: 0.10
expected_effect:
  - improve browser success
  - preserve coding
risk:
  - possible general chat regression
eval_required:
  - browser_heldout_v2
  - coding_regression_v1
  - safety_injection_v1
```

数据混比必须像代码变更一样有版本和理由。

