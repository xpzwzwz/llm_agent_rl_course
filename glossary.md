# 术语表

资料核对日期：2026-05-21。

## Agent

能根据任务目标观察环境、调用工具、更新计划并完成多步任务的模型或系统。

## Action

Agent 对环境执行的动作，例如搜索网页、点击按钮、读文件、运行测试、调用 API。

## Observation

环境返回给 agent 的状态，例如网页内容、工具结果、测试日志、文件内容。

## Trajectory

一次完整任务的执行轨迹，通常包含 observation、action、result、final status。

## Tool Use

模型使用外部工具完成任务的能力。

## Function Calling

让模型按预定义 schema 输出结构化函数调用的机制。

## SFT

Supervised Fine-Tuning，监督微调。用于让模型模仿高质量轨迹。

## DPO

Direct Preference Optimization，直接偏好优化。用 chosen/rejected pair 训练模型偏好更好的输出或轨迹。

## PPO

Proximal Policy Optimization，经典强化学习算法，常用于 RLHF。

## GRPO

Group Relative Policy Optimization，一类用组内相对表现估计优势的 RL 方法，常见于推理模型训练讨论。

## Reward Hacking

模型找到奖励函数漏洞，拿到高 reward 但没有真正完成任务。

## Rejection Sampling

对同一个任务采样多条回答或轨迹，用 verifier 选出成功样本，再把成功样本用于 SFT 或把成功/失败配成 DPO 数据。

## Reference Model

RL 或 DPO 中用来约束当前模型的参考模型，常用于计算 KL 或偏好损失，避免模型偏离过大。

## KL

Kullback-Leibler divergence，常用来衡量当前策略和参考策略的差异。RLHF/GRPO/PPO 中常用 KL 约束控制模型不要训偏。

## Verifier

自动验证器，用来判断任务是否完成，例如测试是否通过、页面状态是否正确。

## Sandbox

受控执行环境，用来限制 agent 的读写权限、固定初始状态、记录日志并支持自动验证。

## Raw Log

Agent 执行时产生的原始日志，包含模型输出、解析后的 action、工具结果、错误和环境版本。

## Chat Template

把 system、user、assistant、tool 等消息转换成模型训练文本的模板。工具调用训练中，chat template 会影响 loss 和格式稳定性。

## Invalid Action

无法解析、工具不存在、参数不合法或越权的 agent 动作。

## Hidden Tests

训练和执行过程中模型看不到的测试，用于防止模型只针对公开测试或删除测试来拿分。

## Advantage

强化学习里衡量某个动作或轨迹比基线好多少的量。PPO 常用 value model 估计基线，GRPO 常用同组样本平均奖励作为基线。

## Value Model

估计当前状态未来期望回报的模型，PPO 中常用于计算 advantage、降低训练方差。

## Policy

策略模型。对 agent 来说，就是根据当前 history 选择下一个 action 或 final 的大模型。

## Rollout

用当前 policy 在环境里采样得到的回答或轨迹。在线 RL 需要不断生成 rollout，再根据 reward 更新 policy。

## Credit Assignment

把最终成功或失败的功劳/责任分配给中间步骤的问题。长程 agent 任务中尤其困难。

## WebArena

真实网页风格的 agent benchmark，用于评估网页环境中的多步任务能力。

## SWE-bench

基于真实 GitHub issue 的软件工程 benchmark，用测试是否通过评估 patch。

## ToolBench

面向工具调用学习和评估的数据集/基准。

## OpenHands

开源软件工程 agent 项目，可用于理解 coding agent 的环境和轨迹。

## browser-use

开源浏览器 agent 项目，可用于网页操作和轨迹采集。
