# 训练过程问题清单

资料核对日期：2026-05-21。参考 RLHF Book、Hugging Face TRL/Alignment Handbook、MOSS-RLHF、OpenRLHF、verl、RLHFlow/Online-RLHF，以及 reward overoptimization 相关研究。

这份文档只讲训练过程问题。先确认数据没有明显污染，再看这里。

## 1. SFT 训练问题

### 1.1 Loss 下降但 Agent 不变强

原因：

- loss 主要来自普通文本，不是 action。
- tool observation 被算进 loss。
- eval 任务和训练目标不一致。
- 训练数据只是模板化轨迹。

排查：

- 看 assistant action token 的 loss。
- 跑 invalid action rate。
- 抽样比较 base 和 SFT 的 trajectory。

### 1.2 模型只会输出自然语言

原因：

- 工具调用样本比例太低。
- action 格式不稳定。
- chat template 没把 tool calling 表达清楚。

处理：

- 增加工具调用轨迹比例。
- 单独做 tool-format SFT。
- 训练后先测 50 个格式任务。

### 1.3 模型过早 Final

原因：

- SFT 数据里很多直接回答。
- 缺少“必须验证”的示范。
- final reward 或偏好数据过度奖励简短回答。

处理：

- 加入先工具后 final 的成功轨迹。
- DPO 中让“未验证 final”作为 rejected。
- eval 增加 `premature_final_rate`。

## 2. DPO 训练问题

### 2.1 DPO 后模型格式崩

原因：

- beta 太小，模型偏离 reference 太快。
- pair 数据格式和 SFT 格式不同。
- chosen/rejected 太长，被截断后丢失关键差异。

处理：

- 增大 beta 或降低学习率。
- 保持 SFT 和 DPO 的 chat template 一致。
- 检查截断后的 chosen/rejected。

### 2.2 DPO 后模型变短、不行动

原因：

- chosen 多是短 final。
- rejected 是长但尝试工具的失败轨迹。
- 偏好数据无意中奖励了“少做少错”。

处理：

- chosen 必须包含有效行动。
- 构造“正确工具轨迹 > 直接 final”的 pair。
- 统计 DPO 后平均 action 数。

### 2.3 Chosen reward 提升但评估不升

原因：

- preference pair 和 eval 任务不同分布。
- DPO 学到风格偏好，不是任务能力。
- rejected 太弱。

处理：

- 增加 hard negative。
- 用 verifier 构造 pair。
- 按任务类型分桶评估。

## 3. PPO / GRPO 训练问题

### 3.1 Reward 上升，Success Rate 不升

这是最高风险信号。

原因：

- reward function 有漏洞。
- reward model 被 over-optimized。
- 模型学会刷过程奖励。
- eval 集和训练环境不一致。

处理：

- 抽查高 reward 失败轨迹。
- 加 hidden tests / hidden checks。
- 降低过程奖励权重。
- 用 held-out verifier 复测。

### 3.2 KL 过高

表现：

- 输出格式变怪。
- 通用能力下降。
- 模型开始输出极端模板。

原因：

- 学习率太高。
- KL penalty 太弱。
- reward 太尖锐。
- 训练步数过多。

处理：

- 降学习率。
- 加强 KL。
- 降低 reward scale。
- 回滚到前一个 checkpoint。

### 3.3 KL 过低但学不动

表现：

- reward 不变。
- success rate 不变。
- 输出和 reference 几乎一样。

原因：

- KL penalty 太强。
- beta / clip 过保守。
- reward 差异太小。

处理：

- 降低 KL 系数。
- 增大采样温度或 num_generations。
- 改 reward，让成功/失败差异更明显。

### 3.4 Entropy 过低

表现：

- 模型总是走同一条路径。
- 对新任务泛化差。
- 多次采样结果高度相似。

处理：

- 增加采样多样性。
- 减少过强 DPO/RL 更新。
- 引入多样成功轨迹。

### 3.5 平均长度或步骤数暴涨

原因：

- 过程奖励太高。
- 没有 cost penalty。
- 模型发现多调用工具能提高分数。

处理：

- 加 step penalty。
- milestone 只奖励一次。
- 对重复动作给负奖励。
- 把 avg_steps 作为核心监控指标。

## 4. Reward Overoptimization

Reward overoptimization 指模型越来越会拿 reward，但真实质量下降。

常见表现：

- reward model 分数持续上升。
- 人工评估下降。
- hidden tests 不升反降。
- 输出越来越模板化。

处理：

- 使用多个 reward / verifier。
- 高分样本人工审计。
- 训练中定期 held-out eval。
- 不把 reward model 当唯一真相。

## 5. 分布式训练和 Rollout 问题

在 OpenRLHF / verl 这类框架里，还会有系统问题：

- rollout 模型和训练模型 checkpoint 不一致。
- reward worker 用了旧 verifier。
- 数据队列混入旧策略样本。
- 多 worker 环境 seed 不一致。
- 失败 rollout 被静默丢弃，造成样本偏差。

排查：

- 每条 trajectory 记录 model checkpoint。
- 记录 reward function version。
- 记录 environment version。
- 统计 rollout failure rate。
- 固定少量任务做可复现回放。

## 6. 训练监控面板

至少监控：

```text
train_loss
eval_success_rate
invalid_action_rate
premature_final_rate
avg_steps
avg_tokens
reward_mean
reward_std
kl
entropy
clip_fraction
hidden_test_pass_rate
cost_per_success
```

判断优先级：

```text
held-out success rate > hidden checks > reward > loss
```

loss 和 reward 都不是最终目标。agent 最终看任务完成率和安全性。

## 7. 额外长尾问题

### 7.1 Reward Std 接近 0

GRPO 需要组内 reward 差异。如果同一组样本全是 0 或全是 1，advantage 信号很弱。

处理：

- 增加 `num_generations`。
- 提高采样温度。
- 改 reward，让部分成功有分。
- 任务难度分桶，避免全易或全难。

### 7.2 Rollout 失败被静默丢弃

如果系统只保留成功生成的 rollout，训练数据会偏向“没有系统错误的任务”。

处理：

- 记录 rollout failure rate。
- 失败也进入日志。
- 区分 model failure 和 infra failure。

### 7.3 Reward Scale 不稳定

不同 reward function 返回范围不同，会导致某个 reward 支配训练。

处理：

- reward normalize。
- 每个 reward 单独记录均值和方差。
- 多 reward 加权时先做 ablation。

### 7.4 Checkpoint Regression

某次训练提升了代码任务，但破坏了网页任务或普通聊天。

处理：

- 每个 checkpoint 跑多任务 eval。
- 保留 base/SFT/DPO/RL 对比。
- 不只用单一 benchmark 选模型。
