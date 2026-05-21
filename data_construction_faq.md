# 数据构造 FAQ

资料核对日期：2026-05-21。参考 TRL、OpenRLHF、verl、LLaMA-Factory、ms-swift、Alignment Handbook、RLHF Book、RewardBench、UltraFeedback/Orca DPO pairs、ToolBench/WebArena/SWE-bench，以及 LLM-as-a-judge 和 agent safety 相关资料。

## 1. SFT 数据

### 1.1 失败轨迹能不能进 SFT？

只有一种情况可以：失败后明确恢复，并最终完成任务。

不能把未恢复失败当示范。未恢复失败更适合做 DPO rejected、错误分析或 RL negative sample。

### 1.2 Tool result 要不要算 loss？

不要。tool result 是环境返回，不是模型应该生成的内容。

SFT 应尽量只对 assistant action/final 算 loss。TRL SFTTrainer 支持 `assistant_only_loss`，但前提是 conversational dataset 和 chat template 能产生 assistant token mask。

### 1.3 Chat template 要不要改？

如果模型 tokenizer 自带模板且支持你的 role，可以先用默认模板。

需要改模板的情况：

- 没有 tool role。
- 不支持 assistant-only loss mask。
- agent training 要求 prefix-preserving template。
- 训练格式和推理格式不一致。

改模板后必须抽样打印渲染后的文本和 loss mask。

### 1.4 SFT 样本太长怎么办？

不要直接从头截断或从尾截断。

保留：

- 原始任务。
- 最近几步。
- 错误恢复关键步骤。
- final 前验证步骤。

早期普通步骤可以压成 state summary。

### 1.5 assistant-only loss 和 max_length 有什么坑？

如果样本超过 `max_length`，截断可能把 assistant mask 截没，导致训练报错或静默丢样本。TRL issue 里就有 `assistant_only_loss=True` 与 sequence truncation 交互导致报错信息不清楚的案例。

处理：

- 训练前模拟 tokenization 和 truncation。
- 统计每条样本截断后是否仍有 assistant label。
- 对长样本先摘要或切分，不要只依赖 trainer 截断。

### 1.6 普通指令数据还要混吗？

要。纯 agent trajectory 可能让模型普通聊天、解释、拒绝能力退化。

起步可以保留 10% 到 25% 普通指令数据，比例根据 eval 调整。

### 1.7 多轮对话里 system prompt 每条都要保留吗？

训练样本里要保留模型推理时实际会看到的 system 规则。不要把训练时有、推理时没有的 system 放进去，否则会造成分布偏移。

### 1.8 VLM / 多模态 SFT 也能 assistant-only loss 吗？

可以，但更容易出错。图像 token、processor 输出、assistant 文本 label mask 要同时正确。TRL issue 里有人专门问 VLM 是否能只训练 assistant text。

处理：

- 明确图像输入不算语言 loss。
- 检查 assistant 文本 token label。
- 抽样 decode labels，确认没有把视觉特殊 token 当目标文本。

### 1.9 SFT 的 packing 能和 completion-only loss 一起用吗？

要看 trainer 和 collator。TRL 早期 issue 里有 `DataCollatorForCompletionOnlyLM` 与 `packing=True` 不兼容的问题。

风险：

- packing 后样本边界混在一起，response mask 可能错。
- 多条对话拼接后，assistant 区间识别失败。

处理：

- 如果要 assistant-only/completion-only loss，先关闭 packing 跑通。
- 如果必须 packing，确认当前 TRL 版本和 chat template 支持正确 mask。
- 抽样检查 packed batch 的 labels。

### 1.10 评估时也能用 completion-only collator 吗？

谨慎。TRL issue 中有人遇到 Seq2SeqTrainer 评估时 masking 与 generation 指标不一致的问题。

处理：

- 训练 loss 的 collator 和生成评估的输入可能需要分开。
- 如果 `predict_with_generate=True`，确认 labels 和 input_ids 没有污染生成输入。
- 用少量样本手工检查 eval decode。

### 1.11 IterableDataset / streaming 数据能直接做 assistant-only loss 吗？

不一定。TRL issue 中有 IterableDataset 与 `assistant_only_loss=True` 交互出错的案例。

处理：

- 起步先用普通 Dataset 验证格式。
- streaming 前先跑 `take(3)` 打印样本。
- 确认 trainer 能读取首条样本判断 conversational format。
- 对 streaming 数据增加独立 schema 校验。

### 1.12 Tool calling SFT 数据需要 `tools` 列吗？

在 TRL dataset format 文档里，tool calling SFT 数据建议包含额外的 `tools` 列。这样 trainer/chat template 才知道可用工具 schema。

处理：

- 每条样本记录可用工具，或在 system prompt 中稳定声明。
- 不要训练时有工具 schema、推理时没有。
- 如果每条任务工具不同，必须保存任务级 tools。

## 2. DPO / Preference 数据

### 2.1 DPO pair 长度差多少算危险？

没有固定绝对值。起步建议监控：

```text
chosen/rejected token ratio > 1.5
```

超过后抽查。如果 chosen 只是更长但没有更正确，应剔除或重标。

### 2.2 DPO pair 必须来自同一个 prompt 吗？

必须。DPO 比较的是同一 prompt 下 chosen 相对 rejected 更好。

不同 prompt 的 pair 会把任务差异误当偏好信号。

### 2.3 chosen/rejected 要不要包含 prompt？

不同框架约定不同，这正是 GitHub issue 中经常出错的地方。

常见两种：

```text
格式 A：prompt 单独一列，chosen/rejected 只放回答
格式 B：chosen/rejected 是完整 messages，里面包含 user prompt
```

处理：

- 先读你使用 trainer 的数据格式说明。
- 不要混用两种格式。
- 训练前用 3 条样本跑完整 preprocessing。
- 检查 prompt 是否被重复拼接。

### 2.4 Rejected 越差越好吗？

不是。太差的 rejected 很容易区分，但学不到细粒度偏好。

更有价值的是 hard negative：

- 格式正确但策略错。
- 做了工具调用但没验证。
- 通过 visible tests 但 hidden tests 失败。
- 看似安全但泄露了隐私。

### 2.5 只有用户点赞/点踩，能不能做 DPO？

不能直接做。

用户反馈要先判断原因：错误、慢、贵、语气、不完整、没有执行工具、还是任务不可完成。最好结合 verifier 或人工复核。

### 2.6 Chosen/rejected 被截断了还能用吗？

谨慎。截断可能删掉关键成功或失败步骤。

训练前要统计：

```text
truncated_pair_rate
chosen_truncated_rate
rejected_truncated_rate
```

被截断 pair 要抽查，必要时改成摘要轨迹。

### 2.7 chosen 和 rejected 的截断策略必须一样吗？

至少要保证二者共享同一个 prompt 前缀。LLaMA-Factory issue 中有人讨论 chosen/rejected cutoff 行为和 Hugging Face DPOTrainer 不一致的问题。

风险：

- chosen 保留了关键上下文，rejected 丢了上下文。
- prompt 被按 chosen 长度截断后拼到 rejected 前，导致比较不公平。

处理：

- 截断前后都保存 token 长度统计。
- 抽查 chosen/rejected 的最终训练文本。
- 长轨迹先摘要，再构造 pair。

### 2.8 DPO 数据格式报错通常是什么原因？

开源框架 issue 中常见原因：

- `chosen` / `rejected` 不是字符串或消息列表。
- 某个 `content` 是 `null`。
- dataset registry 的列名映射错。
- `ranking` / preference 标记没开。
- chat template 不支持当前消息结构。

处理：先写一个 JSONL schema checker，再交给训练框架。

### 2.9 为什么会出现 “Cannot find valid samples”？

常见原因：

- 所有样本在 preprocessing 后被过滤。
- prompt/response 列映射不对。
- chosen/rejected 为空或为 `null`。
- cutoff 后没有可训练 token。
- message role 顺序不符合模板。

处理：

- 用 1 到 5 条样本跑数据加载。
- 打印过滤前后样本数。
- 打印第一条样本渲染后的 prompt/chosen/rejected。

### 2.10 DPO 前要不要先用 chosen 做 SFT？

很多实战文档会建议先对 preference 数据中的 preferred responses 做 SFT，再做 DPO。ms-swift RLHF 文档也建议在 DPO 前先对偏好数据的 preferred responses 做 SFT。

原因：

- 先让模型学会基本格式和行为。
- DPO 更像偏好微调，不适合从零教模型工具协议。

如果 base model 已经很强、格式稳定，可以直接 DPO；但 agent 训练通常建议先 SFT。

### 2.11 ORPO/KTO/SimPO 和 DPO 数据格式一样吗？

不完全一样。

常见：

- DPO/RM/ORPO/CPO/SimPO 多用 `x, y_w, y_l`，即 prompt、preferred、rejected。
- KTO 常用 `x, y, label`，即回答和好/坏标签。

不要把 DPO 数据直接塞给 KTO，除非框架明确支持自动转换。

### 2.12 Preference 数据应该用 explicit prompt 还是 implicit prompt？

TRL dataset format 文档建议 DPO 这类 preference trainer 使用 explicit prompt；RewardTrainer 常见是 implicit prompt。

直觉：

- explicit prompt：`prompt` 单独一列，chosen/rejected 是回答。
- implicit prompt：chosen/rejected 里已经包含完整对话。

处理：

- DPO 起步用 explicit prompt，便于检查同 prompt。
- 如果用 full messages，确认框架不会重复拼 prompt。

### 2.13 偏好数据里能不能有 tie？

多数 DPO 实现只接受 chosen/rejected，不直接接受 tie。

处理：

- tie 样本不要强行构造成 pair。
- 可用于 RM calibration、人工复审或丢弃。
- 如果算法支持 unpaired/tie，再按对应格式使用。

### 2.14 多个 rejected 可以怎么用？

同一 prompt 可以有多个 rejected。

常见做法：

- 构造多个 pair：chosen vs rejected_1, chosen vs rejected_2。
- 或只选 hard negative。
- 或按 reward gap 分层采样。

注意不要让同一 prompt 的重复 pair 过多，导致某些任务权重过大。

### 2.15 DPO 数据里 role 顺序重要吗？

重要。常见错误：

```text
assistant 在 user 前
tool 没有对应 assistant action
最后一条是 user
system 每轮重复插入
```

处理：

- 写 role order checker。
- 对 conversational DPO，chosen/rejected 的 prompt prefix 应一致。

## 3. Reward Model 数据

### 3.1 RM 数据和 DPO 数据能共用吗？

可以部分共用，因为都常用 chosen/rejected pair。

但 RM 更看重泛化和校准。DPO pair 只要能推动当前 policy 偏好，RM pair 还要能让 reward model 对新输出打分可靠。

### 3.2 Pairwise 还是打分制更好？

起步建议 pairwise。标注员通常更容易比较 A/B，而不是给绝对分。

如果用 scalar rating，要做标注员尺度校准。

### 3.3 Reward model 只看 pairwise accuracy 够吗？

不够。

还要看：

- hard negative accuracy。
- length bias。
- domain breakdown。
- 与 verifier 成功率的相关性。
- out-of-distribution 表现。

RewardBench 这类基准的价值就在于用多类 prompt-chosen-rejected trio 检查 RM 泛化。

### 3.4 RM 能不能替代 verifier？

不能。RM 是偏好代理，不是事实裁判。

代码、网页状态、API 结果、数学答案这类任务优先用 deterministic verifier 或 hidden checks。

### 3.5 Reward model 数据要不要包含安全拒绝？

要。否则 RM 可能把“有帮助但危险”的回答打高分。

建议 pair：

```text
安全拒绝 + 提供合规替代 > 直接执行危险请求
```

### 3.6 Reward model 数据需要覆盖当前 policy 吗？

需要。RM 如果只看过早期模型输出，后续 PPO/GRPO 的新型输出可能 OOD，容易被 over-optimize。

处理：

- 定期加入当前 policy 采样。
- 加 hard negatives。
- held-out RM eval 按 checkpoint 来源分桶。

## 4. GRPO / PPO / RL Prompt 数据

### 4.1 GRPO prompt set 要存什么字段？

至少：

```text
prompt
task_id
environment
tools
max_steps
verifier
reward_config
```

verl 等框架常把 prompt、data source、ability、reward model / ground truth、extra metadata 放入标准化数据格式。

### 4.2 GRPO 自定义数据里的 extra fields 会不会丢？

可能。ms-swift issue 中有人报告自定义数据的额外字段在 GRPO 中导致 tokenizer error 或被丢弃。

处理：

- 明确哪些字段会传给 reward function。
- 不要假设所有 metadata 都能穿过 trainer。
- 写最小样本测试 reward function 是否收到字段。
- 必要时把 reward 所需 metadata 放进框架认可的字段。

### 4.3 GRPO 组内 reward 全一样怎么办？

这组样本没有有效相对优势信号。

处理：

- 增加 `num_generations`。
- 提高采样温度。
- 改 reward，让部分成功有分。
- 过滤全 0 或全 1 的 prompt。
- 按任务难度分桶。

### 4.4 On-policy 数据能不能回流 SFT/DPO？

可以，但要记录生成模型版本和采样参数。

建议：

- 成功 rollout -> SFT 候选。
- 成功/失败 rollout -> DPO pair。
- 失败 rollout -> failure analysis。

不要让旧 policy 的低质量 rollout 长期污染新模型。

### 4.5 PPO/GRPO prompt 能不能和 eval prompt 重叠？

不能。训练 prompt 和 eval prompt 必须按 task_id 隔离。

否则在线采样会把 eval 变成训练集。

### 4.6 Reward function 需要哪些数据字段？

至少要能拿到：

- 模型 completion 或 trajectory。
- task_id。
- ground truth 或 verifier 配置。
- 环境状态或环境 ID。
- 安全规则。

如果 reward function 只能看到 final text，看不到工具真实执行结果，它很容易被模型骗。

### 4.7 RL rollout 后端版本会影响数据吗？

会。OpenRLHF issue 中有人报告 vLLM 版本变化导致 RL sampling reward 不稳定、不可复现。

数据层要记录：

- rollout backend。
- backend version。
- sampling args。
- seed。
- model checkpoint。

否则同一 prompt 生成的 rollout 差异无法追踪。

### 4.8 RL prompt set 要不要包含太容易的任务？

要少量保留作为 sanity check，但不能占比太高。

如果任务太容易，同组 reward 全是 1；如果太难，全是 0。两者都不利于 GRPO。

### 4.9 Online DPO 和离线 DPO 的数据差别是什么？

离线 DPO 用固定 preference pair。Online DPO 会用当前模型采样新回答，再由 reward/judge/verifier 生成新偏好。

Online 数据必须记录：

- policy checkpoint。
- sampling args。
- judge/verifier version。
- pair creation time。

否则数据回流后不可审计。

## 5. Agent Trajectory 数据

### 5.1 Tool result 太长怎么办？

可以摘要，但要保留：

- 来源。
- 关键错误。
- 关键字段。
- 截断标记。
- raw_ref。

不要摘要成“返回了一些相关信息”。

### 5.2 Hidden tests 结果能不能给标注员看？

一般不要给普通标注员看。hidden 信息容易泄漏到训练数据。

如果需要专家复审，只能在受控界面显示，并确保不会进入 model-visible 字段。

### 5.3 同一任务多条轨迹怎么 split？

按 task_id split。

不要让同一 task 的成功轨迹在 train、失败轨迹在 eval。

### 5.4 搜索结果、网页、GitHub issue 会变，怎么办？

记录 provenance 和环境快照：

- URL。
- captured_at。
- 页面文本或摘要。
- repo commit。
- tool version。
- raw_ref。

不可复现数据只能低权重使用或用于分析。

### 5.5 Agent 看到网页里的恶意指令，数据怎么标？

如果模型执行了恶意指令：不要进 SFT。可作为 DPO rejected 或 safety negative。

如果模型识别并忽略恶意指令：可作为安全 SFT / chosen。

### 5.6 轨迹中工具调用失败要不要删？

不要无脑删。工具失败后成功恢复是高价值 SFT 数据。

但如果最终未恢复，不要进 SFT，可进入：

- DPO rejected。
- 错误分析。
- targeted data generation。

### 5.7 多 agent 对话怎么构造数据？

要记录每个 agent 的 role、权限和可见上下文。

注意：

- 不同 agent 的私有 memory 不应混入其他 agent 可见内容。
- shared scratchpad 要标 provenance。
- 敏感信息跨 agent 流动要审计。

### 5.8 Tool schema 更新后旧数据怎么办？

不要直接混用。

处理：

- 标记 `tool_schema_version`。
- 旧数据转换到新 schema，或降权/退役。
- format warmup 保留少量新 schema 样本。
- eval 只用当前线上 schema。

### 5.9 工具返回的错误栈要保留吗？

保留关键信息，但要脱敏和摘要。

建议：

- 错误类型。
- 文件/函数/状态码。
- 最小复现信息。
- raw_ref。

不要保留 secret、内部路径、用户隐私。

### 5.10 Agent 数据里要不要保留 cost？

要。cost 是 agent 质量的一部分。

记录：

- steps。
- tokens。
- tool calls。
- wall time。
- money cost。

DPO/RL 可以构造“同样成功但更低成本”的偏好。

## 6. 标注和 Judge

### 6.1 LLM judge 能不能直接用？

可以用于初筛，不建议作为唯一标签。

优先级：

```text
deterministic verifier > hidden tests > human review > multi-judge > single judge
```

### 6.2 标注员冲突多怎么办？

先不要急着训练。

处理：

- 检查标注指南是否模糊。
- 加 gold questions。
- 对冲突样本专家仲裁。
- 冲突率高的样本降权或剔除。

### 6.3 标注员能不能看到模型名字？

最好不要。模型名字会引入偏见。

如果必须展示，至少在数据里记录，后续分析是否存在 generator/judge/source bias。

### 6.4 Preference reason 要不要保留？

要。它能帮助审计偏好质量、训练 reward model、定位标注冲突。

但 reason 不一定直接进入 DPO 训练，除非你的训练目标明确使用解释。

### 6.5 Judge prompt 要不要版本化？

必须版本化。Judge prompt 变化会导致偏好分布变化。

记录：

- judge model。
- judge prompt version。
- scoring rubric。
- position swap 是否启用。
- 是否使用 chain-of-thought 隐式推理。

### 6.6 人类标注和 LLM judge 冲突怎么办？

不要简单平均。

处理：

- verifier 可判定时，以 verifier 为准。
- 高风险任务交专家复审。
- 记录 conflict type。
- 冲突样本可作为 judge 质量评估集。

## 7. Synthetic Data 和混比

### 7.1 Synthetic data 占比多少合理？

没有通用答案。早期实验可以较高，但 unverified synthetic 应低权重。

建议：

- 有 verifier 的 synthetic 可以较高。
- 无 verifier 的 synthetic 要抽查和降权。
- 关键评估必须用 held-out 真实任务。

### 7.2 Synthetic data 怎么发现模板化？

看：

- prompt n-gram 重复。
- action path 重复。
- final 模板重复。
- 同一 generator 产生的样本占比。
- 任务难度是否过于理想。

模板化严重时降权或重采。

### 7.3 数据混比怎么调？

每次只改一个主要变量：

```text
browser 20% -> 30%
hard negative 10% -> 20%
synthetic 50% -> 30%
```

同时跑分场景 eval。不要一次性换混比、学习率和 reward。

### 7.4 合成数据的 generator model 要记录吗？

必须记录。

至少记录：

- generator model。
- prompt template。
- temperature。
- verifier version。
- human audit rate。

否则后面无法解释某类模板化或偏差来自哪里。

### 7.5 公开数据集可以直接混进业务 agent 数据吗？

谨慎。公开数据集适合补通用能力、学习格式或做 baseline，但业务 agent 需要自己的工具、环境和 verifier。

混入前检查：

- license。
- 数据域是否匹配。
- 是否和 eval benchmark 重叠。
- 格式是否会污染工具协议。

### 7.6 数据去重要做到什么粒度？

至少三层：

- exact duplicate。
- near-duplicate prompt。
- same task / same issue / same webpage template。

Agent 任务尤其要按 task_id 和环境实体去重，不只是按文本去重。

### 7.7 数据多样性怎么衡量？

可以看：

- task type 分布。
- tool sequence 分布。
- difficulty 分布。
- success/failure 分布。
- generator model 分布。
- domain/source 分布。

只看样本数没有意义。

## 8. 数据版本和回滚

### 8.1 数据版本什么时候该回滚？

出现以下情况应回滚或暂停：

- 安全指标下降。
- hidden eval 下降明显。
- reward 上升但人工评估下降。
- 某一关键业务域 regression。
- 发现 P0 数据问题。

### 8.2 公开 benchmark 数据能不能进训练？

除非你明确不再用它评估，否则不要进训练。

公开 benchmark 更适合学习格式和做参考，不适合作为唯一训练/评估依据。

### 8.3 数据集 card 必须写吗？

正式训练必须写。否则后续无法解释模型变化。

至少记录：

- 来源。
- 版本。
- 样本数。
- split 方法。
- 过滤规则。
- 已知限制。
- 隐私清洗。

### 8.4 一批数据质量不好，是修数据还是调训练参数？

先修数据。

如果存在 P0/P1 数据问题，例如泄漏、标签错、格式错、prompt 不一致，调参没有意义。

### 8.5 训练数据和评估数据来自同一公开数据集怎么办？

要拆清楚用途。

如果某公开数据集用于训练，就不要再把它的同源任务作为主要评估。可以保留作 sanity check，但必须有私有 held-out 或新采集 eval。

### 8.6 数据发布前最小检查是什么？

最小检查：

```text
schema check
secret scan
task_id split overlap
role order check
empty/null content check
length/truncation stats
sample render check
manual audit
dataset card
change log
```
