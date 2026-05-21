# 第十四课：Agent RLHF 的技术原理

这一课不追求论文级推导，而是让你知道 SFT、DPO、PPO、GRPO 分别在优化什么、为什么需要 reference model、为什么 reward 会把模型训偏。

## 1. 统一视角：模型是策略

对 agent 来说，模型不是“回答器”，而是策略：

```text
policy: pi_theta(action | history)
```

`history` 包含任务、已有 observation、历史 action 和 tool result。模型每一步根据 history 选择下一个 action 或 final。

整条轨迹的概率可以写成：

```text
pi_theta(trajectory | task)
= product over t pi_theta(action_t | history_t)
```

训练的本质就是提高好轨迹的概率，降低坏轨迹的概率，同时不要让模型偏离太远。

## 2. SFT：最大化示范轨迹概率

SFT 的目标是让模型模仿示范数据。

简化写法：

```text
L_SFT(theta) = - sum log pi_theta(y_t | x, y_<t)
```

也就是普通 next-token loss。对 agent 来说，`y_t` 主要应该是 assistant 的 action/final token，而不是 user 或 tool token。

所以 agent SFT 的关键不是公式，而是 mask：

```text
user/task/context: 不算 loss
tool observation: 不算 loss
assistant action/final: 算 loss
```

如果把 tool observation 也算 loss，模型会学会“生成 observation”，这会导致伪造工具结果。

TRL 的 SFTTrainer 支持 conversational dataset 和 `assistant_only_loss`，这正是 agent SFT 需要关注的点。

## 3. Reward Model：把偏好变成分数

经典 RLHF 会训练 reward model：

```text
r_phi(task, response) -> scalar score
```

偏好数据是：

```text
chosen > rejected
```

reward model 训练目标是让：

```text
r_phi(chosen) > r_phi(rejected)
```

常见 pairwise loss 直觉：

```text
loss = -log sigmoid(r_chosen - r_rejected)
```

如果 chosen 分数只比 rejected 高一点，loss 还会推动差距变大；如果 chosen 已经明显更高，loss 就小。

对 agent 来说，reward model 可以给整条 trajectory 打分。但只要有自动 verifier，优先用 verifier，因为它更可解释、更难被漂亮文字骗过。

## 4. DPO：不用显式 Reward Model 的偏好优化

DPO 的核心想法是：不用先训练 reward model，再 PPO；可以直接用 preference pair 更新 policy。

DPO 比较的是：

```text
模型对 chosen 的 logprob - 模型对 rejected 的 logprob
```

同时还要减去 reference model 的同样差值，避免模型只是利用原本就高概率的回答。

直觉公式：

```text
logit =
  beta * [
    log pi_theta(chosen | prompt)
  - log pi_theta(rejected | prompt)
  - log pi_ref(chosen | prompt)
  + log pi_ref(rejected | prompt)
  ]

loss = -log sigmoid(logit)
```

解释：

- `pi_theta` 是当前训练模型。
- `pi_ref` 是参考模型，通常是 SFT 模型。
- `chosen` 应该比 `rejected` 概率更高。
- `beta` 控制偏好学习强度和偏离 reference 的程度。

`beta` 太大，模型更保守，学得慢；`beta` 太小，模型可能偏离太快，格式和通用能力变差。

Agent DPO 的关键是：chosen/rejected 必须是整条轨迹，不只是 final answer。

## 5. PPO：带约束的在线策略优化

PPO 直接优化 reward：

```text
maximize E[reward(task, trajectory)]
```

但如果只追 reward，模型会快速训飞，所以 PPO 使用两个关键机制：

1. ratio clipping：限制每次更新不要太大。
2. KL penalty：限制新策略不要离 reference model 太远。

策略比率：

```text
ratio = pi_theta(action | history) / pi_old(action | history)
```

PPO 裁剪目标直觉：

```text
min(ratio * advantage, clip(ratio, 1-eps, 1+eps) * advantage)
```

`advantage` 表示这个 action 比预期好多少。

PPO 还常用 value model：

```text
V(history) -> expected future reward
```

然后：

```text
advantage = actual_return - V(history)
```

value model 的作用是降低方差，告诉训练过程“这一步到底比预期好多少”。

对 agent 来说，PPO 工程复杂，因为它需要 policy、reference、reward、value 多个模型或模块协同。OpenRLHF 和 verl 这类项目适合学习这条生产级数据流。

## 6. GRPO：组内相对优势

GRPO 的直觉是：对同一个 prompt 采样多条 completion 或 trajectory，然后在组内比较。

流程：

```text
prompt -> sample G trajectories -> reward each trajectory
       -> compute group mean/std
       -> advantage_i = (reward_i - mean_reward) / std_reward
       -> increase high-advantage trajectories
```

它的好处是可以减少或省掉单独的 value model。因为同一组样本的平均表现可以作为 baseline。

这非常适合可验证任务：

- 数学题：答案对不对。
- 代码题：测试过不过。
- 网页任务：最终状态是否满足。
- API 任务：返回和数据库状态是否正确。

Agent GRPO 的关键是 reward function。组内比较再好，如果 reward 错了，模型还是会学错。

## 7. KL 为什么重要

KL 衡量两个分布差多远：

```text
KL(pi_theta || pi_ref)
```

在 RLHF/GRPO/PPO 里，reference model 通常是 SFT 模型。KL 的作用：

- 保持语言和格式能力。
- 防止模型为了 reward 走极端。
- 降低 reward hacking。
- 让更新更稳定。

如果 KL 太强，模型学不动；如果 KL 太弱，模型容易训飞。

## 8. Offline Preference 和 Online RL 的区别

DPO 是 offline preference optimization：

```text
固定数据集里的 chosen/rejected -> 更新模型
```

GRPO/PPO 是 online 或 semi-online RL：

```text
当前模型采样新轨迹 -> 环境给 reward -> 更新模型
```

区别：

- DPO 稳定、便宜，但受限于已有数据。
- Online RL 能探索新策略，但更贵、更容易 reward hacking。
- Rejection sampling 介于中间，常用于从 offline 过渡到 online。

工程上，不要把 DPO 和 RL 对立起来。常见路线是：

```text
SFT -> DPO -> rejection sampling -> GRPO/PPO
```

## 9. 用开源项目学原理

建议这样对应：

- TRL：看 SFTTrainer、DPOTrainer、GRPOTrainer，理解最小 API 和数据格式。
- LLaMA-Factory：看配置化 SFT/DPO/GRPO，理解训练参数怎么落到 YAML。
- OpenRLHF：看 SFT -> RM -> PPO/DPO 全流程和 Ray/vLLM 角色拆分。
- verl：看 PPO/GRPO 的 rollout、reward、advantage、update 在生产框架里怎么分离。
- Axolotl：看大规模 SFT/DPO 数据配置和多模型训练实践。

不要只读论文公式。把公式和开源框架里的 dataset、trainer、rollout、reward function 对上，原理才会变成工程能力。

