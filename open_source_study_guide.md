# 开源项目学习路线

资料核对日期：2026-05-21。本页结合 GitHub API 查询和公开文档，安排一条从小实验到生产级 RLHF/Agent RL 的学习路线。

## 1. 项目速览

以下数据为 2026-05-21 在本机通过 GitHub API 查询：

```text
hiyouga/LlamaFactory: 71,469 stars, pushed_at 2026-05-21
verl-project/verl: 21,460 stars, pushed_at 2026-05-21
huggingface/trl: 18,429 stars, pushed_at 2026-05-21
modelscope/ms-swift: 14,207 stars, pushed_at 2026-05-21
axolotl-ai-cloud/axolotl: 11,950 stars, pushed_at 2026-05-21
OpenRLHF/OpenRLHF: 9,529 stars, pushed_at 2026-05-15
CarperAI/trlx: 4,749 stars, pushed_at 2024-01-08
policy-gradient/GRPO-Zero: 1,848 stars, pushed_at 2025-04-18
OpenLMLab/MOSS-RLHF: 1,428 stars, pushed_at 2024-03-03
RLHFlow/Online-RLHF: 545 stars, pushed_at 2024-12-28
ash80/RLHF_in_notebooks: 245 stars, pushed_at 2025-06-20
```

这些 stars 不是技术优劣排名，只是生态活跃度参考。

## 2. 先看教学型项目

如果目标是理解技术原理，先看小项目：

- `ash80/RLHF_in_notebooks`：三份 notebook 讲 SFT、reward model、PPO。
- `OpenLMLab/MOSS-RLHF`：重点解释 LLM RLHF 里的 PPO。
- `policy-gradient/GRPO-Zero`：从零实现 GRPO，适合理解组内相对优势。
- `RLHFlow/Online-RLHF`：在线 RLHF 和迭代 DPO recipe。
- `kttian/factual_dpo`：DPO reference implementation。

这些项目不一定最活跃，但比生产框架更适合回答“loss 到底怎么算”。

更详细的学习安排见 [原理学习项目推荐](principle_learning_projects.md)。

## 3. 第一站：TRL

仓库：

```text
https://github.com/huggingface/trl
```

适合学习：

- SFTTrainer 数据格式。
- DPOTrainer 的 prompt/chosen/rejected。
- GRPOTrainer 的 reward function。
- PPOTrainer 的基本指标。

怎么学：

1. 先跑 SFTTrainer 小例子。
2. 把课程 toy project 的 `sft.jsonl` 改成 TRL messages 格式。
3. 再跑 DPOTrainer，理解 `beta` 和 reference model。
4. 最后看 GRPOTrainer 的 reward function 接口。

TRL 的价值是最小闭环清楚，适合把概念和代码对上。

## 4. 第二站：LLaMA-Factory

仓库：

```text
https://github.com/hiyouga/LLaMA-Factory
```

适合学习：

- 配置化 SFT/DPO/GRPO。
- LoRA/QLoRA 参数。
- 多模型、多数据集训练配置。
- 从命令行跑 alignment 实验。

怎么学：

1. 找 SFT 配置，理解 dataset、template、cutoff_len。
2. 找 DPO 配置，理解 preference dataset 怎么声明。
3. 找 GRPO/PPO 相关配置，理解 reward 和 rollout 参数。
4. 对比课程 `training_recipes.md` 里的伪代码，看配置项对应哪个概念。

LLaMA-Factory 适合把“我要训练一个模型”变成可运行命令。

## 5. 第三站：ms-swift

仓库：

```text
https://github.com/modelscope/ms-swift
```

适合学习：

- 中文模型生态里的 SFT/DPO/GRPO。
- Qwen、DeepSeek、InternLM 等模型训练。
- PEFT 和全参数训练。
- 从教学代码过渡到可复现实验命令。

怎么学：

1. 先找 SFT 示例。
2. 再找 DPO 示例。
3. 最后看 GRPO/RLHF 示例。
4. 关注数据集格式和命令行参数。

## 6. 第四站：Axolotl

仓库：

```text
https://github.com/axolotl-ai-cloud/axolotl
```

适合学习：

- 大规模 SFT/DPO 数据配置。
- packing、sequence length、LoRA、FSDP/DeepSpeed。
- 数据混合和训练工程参数。

怎么学：

1. 看 YAML 配置。
2. 找 dataset 格式说明。
3. 关注训练稳定性参数，而不是只看算法名。

Axolotl 更偏训练工程，适合补“怎么把数据高效喂进去”。

## 7. 第五站：OpenRLHF

仓库：

```text
https://github.com/OpenRLHF/OpenRLHF
```

适合学习：

- SFT -> Reward Model -> PPO。
- DPO / rejection sampling。
- Ray + vLLM 的 RLHF 训练架构。
- policy、reference、reward、critic 多角色协同。

怎么学：

1. 看 basic training pipeline。
2. 看 SFT 脚本。
3. 看 reward model 脚本。
4. 看 PPO 脚本，画出每个模型角色。
5. 再看 DPO 脚本，对比为什么 DPO 省掉 RM/PPO。

OpenRLHF 适合理解经典 RLHF 的生产复杂度。

## 8. 第六站：verl

仓库：

```text
https://github.com/verl-project/verl
```

适合学习：

- PPO/GRPO/DAPO 等 RL post-training。
- rollout、reward、advantage、update 的模块拆分。
- 分布式 worker 和资源池。
- HybridFlow 这类生产级抽象。

怎么学：

1. 看 PPO example architecture。
2. 找 data preprocess 到 parquet 的流程。
3. 看 rollout worker 怎么生成样本。
4. 看 reward function 怎么接入。
5. 看 advantage 在哪里计算。
6. 对照第十四课和第十五课，把公式对应到代码模块。

verl 适合学习“RL 训练系统长什么样”。

## 9. 历史参考：trlx

仓库：

```text
https://github.com/CarperAI/trlx
```

trlx 是较早的 RLHF 开源项目，适合了解历史实现和早期 PPO/RLHF 设计。但从活跃度看，今天学习新项目应优先 TRL、OpenRLHF 和 verl。

## 10. Agent 项目怎么接上训练项目

训练框架解决的是：

```text
给定数据和 reward，怎么更新模型
```

Agent 框架解决的是：

```text
怎么在环境里生成轨迹
```

推荐组合：

```text
browser-use / WebArena -> 采集网页轨迹 -> TRL/verl GRPO
OpenHands / SWE-bench -> 采集代码轨迹 -> DPO/GRPO
LangGraph / AutoGen -> 业务工具轨迹 -> SFT/DPO
```

不要指望一个项目解决所有问题。通常需要：

- Agent runner 采集轨迹。
- Verifier 打分。
- Dataset builder 转 SFT/DPO/RL 格式。
- TRL/OpenRLHF/verl 训练。
- Benchmark runner 回归评估。

## 11. 推荐学习顺序

```text
课程 toy_project
-> RLHF_in_notebooks / GRPO-Zero 这类原理项目
-> TRL SFT/DPO/GRPO 小实验
-> ms-swift 或 LLaMA-Factory 配置化训练
-> OpenRLHF 经典 RLHF 全流程
-> verl 生产级 PPO/GRPO 架构
-> 接入 OpenHands/browser-use 真实 agent 轨迹
```

学到最后，你应该能回答：

- 数据在哪一步变成 logprob loss？
- reward 在哪里计算？
- reference model 在哪里用？
- advantage 在哪里算？
- rollout 和 train 是同步还是异步？
- verifier 错了会怎样污染训练？
