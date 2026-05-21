# 原理学习项目推荐

资料核对日期：2026-05-21。本页专门收集更适合“看懂原理”的 GitHub 项目。它们不一定是最强生产框架，但比大型框架更适合学习 SFT、Reward Model、PPO、DPO、GRPO 的核心机制。

## 1. 先分清两类项目

教学型项目：

```text
目标：看懂算法怎么从数据变成 loss，再变成模型更新
特点：notebook、单机脚本、代码少、抽象少
```

生产型项目：

```text
目标：高效训练大模型
特点：Ray/vLLM/DeepSpeed/FSDP、多 worker、配置复杂
```

学习原理时，顺序应该是：

```text
教学型项目 -> 小框架 TRL -> 配置化框架 -> 生产级 RL 框架
```

不要一开始读 verl/OpenRLHF 的分布式 PPO。那会把注意力耗在工程调度上，而不是 loss 和数据流。

## 2. RLHF_in_notebooks：三阶段 RLHF 入门

仓库：

```text
https://github.com/ash80/RLHF_in_notebooks
```

GitHub API 查询：245 stars，2025-06-20 更新。描述是用 3 个 Jupyter notebooks 分步演示 RLHF，包括 SFT、reward model 和 PPO。

适合学习：

- SFT 数据怎么喂进模型。
- Reward model 怎么从偏好数据学分数。
- PPO 如何用 reward 更新语言模型。

建议看法：

1. 先看 SFT notebook，确认它和第十四课的 next-token loss 对应。
2. 再看 reward model notebook，对应 pairwise preference loss。
3. 最后看 PPO notebook，对应 policy、reward、value、KL。

这是“从零看 RLHF 三段式”的好入口。

## 3. MOSS-RLHF：理解 PPO 细节

仓库：

```text
https://github.com/OpenLMLab/MOSS-RLHF
```

GitHub API 查询：1,428 stars，2024-03-03 更新。项目标题是 “Secrets of RLHF in Large Language Models Part I: PPO”。

适合学习：

- PPO 在 LLM 里的细节。
- reward、KL、advantage、value 的关系。
- RLHF 为什么比 SFT/DPO 更难稳定。

建议看法：

1. 先读项目 README 的 PPO 解释。
2. 对照第十四课里的 PPO ratio、advantage、KL。
3. 关注训练指标，而不是只看最终效果。

MOSS-RLHF 适合补 PPO 原理，不适合作为今天生产训练的首选框架。

## 4. GRPO-Zero：从零看 GRPO

仓库：

```text
https://github.com/policy-gradient/GRPO-Zero
```

GitHub API 查询：1,848 stars，2025-04-18 更新。描述是从零实现 DeepSeek-R1 的 GRPO 算法。

适合学习：

- 同一 prompt 多条采样。
- 组内 reward 均值/方差。
- group-relative advantage。
- KL 约束和 policy update。

建议看法：

1. 找 sampling 部分：同一题采样多少条。
2. 找 reward 计算：答案如何被 verifier 打分。
3. 找 advantage 计算：组内相对值怎么来。
4. 找 loss：高 reward completion 如何被增强。

这类项目比生产框架更适合理解 GRPO 为什么“不一定需要 value model”。

## 5. RLHFlow / Online-RLHF：在线 RLHF 和迭代 DPO

仓库：

```text
https://github.com/RLHFlow/Online-RLHF
```

GitHub API 查询：545 stars，2024-12-28 更新。描述是 online RLHF 和 online iterative DPO 的 recipe。

适合学习：

- offline DPO 和 online DPO 的区别。
- 采样、打分、再训练的循环。
- rejection sampling 和 iterative preference learning。

建议看法：

1. 看数据如何从当前模型采样得到。
2. 看 reward / judge 如何筛选。
3. 看新数据如何回流到训练。

这和 agent 训练很接近，因为 agent 本来就需要不断在环境中采样 trajectory。

## 6. factual_dpo：DPO Reference Implementation

仓库：

```text
https://github.com/kttian/factual_dpo
```

GitHub API 查询：0 stars，2024-05-02 更新。虽然不活跃，但描述明确是 DPO reference implementation。

适合学习：

- prompt/chosen/rejected 数据结构。
- DPO loss 如何落到代码。
- reference model logprob 的作用。

这类小项目 stars 少也可以看，因为目标是理解最小实现，不是找生产工具。

## 7. ms-swift：配置化 SFT/DPO/GRPO 实战

仓库：

```text
https://github.com/modelscope/ms-swift
```

GitHub API 查询：14,207 stars，2026-05-21 更新。描述包含 PEFT、Full-parameter、CPT、SFT、DPO、GRPO 和大量 LLM/VLM 支持。

适合学习：

- 配置化跑 SFT/DPO/GRPO。
- Qwen/DeepSeek 等中文生态模型训练。
- 从教学代码过渡到可用工具链。

建议看法：

1. 先看 SFT 示例。
2. 再看 DPO 示例。
3. 最后看 GRPO/RLHF 示例。
4. 对照课程 toy project 的数据格式，理解需要怎么转换。

## 8. 学习顺序建议

如果你想真正讲清原理，建议课程学习顺序改成：

```text
第十四课：先懂损失函数直觉
-> RLHF_in_notebooks：跑 SFT/RM/PPO 三段式
-> factual_dpo：看 DPO 最小实现
-> GRPO-Zero：看 GRPO 从零实现
-> RLHFlow Online-RLHF：看采样-筛选-再训练循环
-> TRL：用标准库复现小实验
-> ms-swift / LLaMA-Factory：转配置化训练
-> OpenRLHF / verl：看生产级分布式 RL
```

对 agent 课程来说，最关键的不是读完所有项目，而是把每个项目映射到一个问题：

```text
SFT：示范轨迹如何变成 token loss？
DPO：chosen/rejected 如何变成 logprob ratio？
PPO：reward 如何通过 advantage 更新 policy？
GRPO：同组多条轨迹如何产生相对优势？
Agent：环境 verifier 如何产生可靠 reward？
```

