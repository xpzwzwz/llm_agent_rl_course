# 第十五课：长程 Agent 的 Credit Assignment

## 1. 问题是什么

长程 agent 任务常常是：

```text
20 步动作后，最终成功或失败
```

如果最后成功，哪些步骤有贡献？如果最后失败，哪一步是根因？

这就是 credit assignment：把最终结果的功劳或责任分配给中间动作。

## 2. 单轮回答没有这个问题吗

普通回答也有 token-level credit assignment，但训练信号比较密：

```text
每个 token 都有 next-token label
```

Agent RL 的信号更稀疏：

```text
第 1 到 19 步没有明确 reward
第 20 步 verifier 给 0 或 1
```

这会带来两个问题：

- 高方差：同样策略有时成功有时失败。
- 错误归因：模型可能强化了无关步骤。

## 3. Trajectory-level Preference

DPO 常把整条轨迹当作 chosen/rejected：

```text
good trajectory > bad trajectory
```

优点是简单稳定。缺点是信号粗：

```text
good 轨迹里的每一步都被提升
bad 轨迹里的每一步都被压低
```

但真实情况可能是：

- good 轨迹里有冗余步骤。
- bad 轨迹前半段很好，只是最后一步错。

所以 DPO 后还需要错误分析和更细粒度数据。

## 4. Step-level Reward

过程奖励可以缓解稀疏 reward：

```text
到达正确页面 +0.2
找到相关文件 +0.2
运行测试 +0.2
最终通过 +1.0
```

但过程奖励很危险。它会鼓励模型刷步骤：

```text
反复运行测试
反复搜索
反复打开相关文件
```

设计过程奖励的原则：

- milestone 只奖励一次。
- final success 权重最高。
- 重复动作要惩罚。
- 过程奖励必须和最终成功正相关。

## 5. Advantage 的作用

PPO/GRPO 里的 advantage 试图回答：

```text
这个 action/trajectory 比基线好多少？
```

PPO 用 value model 估计基线：

```text
advantage = return - V(history)
```

GRPO 用组内平均作为基线：

```text
advantage_i = reward_i - mean(group_rewards)
```

对长程 agent 来说，advantage 能降低方差，但不能自动解决 reward 错误。如果 verifier 错了，advantage 只是更稳定地学错。

## 6. Agent 里的状态别名问题

有时两个 history 看起来相似，但真实环境状态不同：

```text
页面文本类似，但登录态不同
文件内容类似，但 patch 已经应用
测试输出类似，但失败原因不同
```

这叫状态别名。模型如果只看到摘要 observation，可能不知道自己处在哪个状态。

解决：

- observation 包含必要状态 ID。
- 工具返回结构化结果。
- 关键环境状态进入日志。
- 长任务定期让模型显式列出已完成事项。

## 7. Memory 和 Context

长程 agent 还会遇到上下文限制。完整 trajectory 太长时，模型看不到早期信息。

常见做法：

- 滚动摘要。
- scratchpad 状态。
- 外部 memory。
- 任务 checklist。
- 检索历史步骤。

训练时要让模型学会维护状态，而不是只依赖完整上下文。

## 8. Verifier 的局限

Verifier 只能检查你写进去的条件。

代码任务：

```text
visible tests pass
```

不代表：

```text
hidden behavior correct
patch 简洁
没有安全问题
```

网页任务：

```text
页面出现 expected text
```

不代表：

```text
没有误提交其他表单
没有越权访问
状态真的持久化
```

所以 verifier 要和人工抽查、hidden tests、规则约束结合。

## 9. 长程 Agent 的训练策略

推荐顺序：

1. 先训练短任务，确保工具格式稳定。
2. 加入 3 到 5 步任务，训练 observation -> action。
3. 加入失败恢复轨迹。
4. 加入 checklist / state summary 训练。
5. 用 DPO 惩罚提前结束和重复动作。
6. 用 GRPO/PPO 优化最终成功率。
7. 用 held-out 长任务评估泛化。

不要直接从 50 步任务开始 RL。那样 debug 空间太大。

## 10. 开源项目怎么帮助理解

TRL 适合看小规模 GRPO：同一 prompt 多条 completion 怎么进入 reward function。

verl 适合看生产级 rollout：生成、打分、advantage、更新如何拆成不同 worker。

OpenRLHF 适合看 PPO 角色分工：policy、reference、reward、critic/value 如何协同。

OpenHands 和 browser-use 适合采集长程真实轨迹：它们让你看到 agent 失败不是公式问题，而是工具、环境、状态和恢复问题。

把这些项目合起来看，才能理解：长程 agent 的难点不是某一个 loss，而是训练信号、环境状态和工程约束的组合。

