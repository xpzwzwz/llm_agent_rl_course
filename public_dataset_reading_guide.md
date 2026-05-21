# 公开数据集导读

这份文档说明公开数据集适合学什么，以及不能直接照搬什么。

## 1. UltraFeedback / UltraFeedback Binarized

链接：

```text
https://huggingface.co/datasets/HuggingFaceH4/ultrafeedback_binarized
```

适合学习：

- preference pair 长什么样。
- chosen/rejected 如何组织。
- judge 标注如何变成 DPO 数据。

注意：

- 它主要是文本回答偏好，不是完整 agent trajectory。
- 不要直接把它当工具调用数据。
- 要关注 chosen/rejected 长度差和 judge 偏差。

看数据时重点看：

- prompt。
- chosen。
- rejected。
- score / rating 字段。
- 消息格式。

## 2. Orca DPO Pairs

链接：

```text
https://huggingface.co/datasets/HuggingFaceH4/orca_dpo_pairs
```

适合学习：

- 指令数据如何转成 preference pair。
- DPO 数据的基本字段。
- 不同回答质量的对比。

注意：

- 它不解决 agent 工具使用问题。
- 不能学到 observation-action-result 结构。

## 3. ToolBench

链接：

```text
https://github.com/OpenBMB/ToolBench
```

适合学习：

- 工具调用任务如何构造。
- 多 API 调用链。
- 工具选择和参数生成。

注意：

- 真实业务工具 schema 可能更严格。
- API 返回和权限边界需要自己重建。
- 不要只学单步 function calling，要看调用链。

## 4. WebArena

链接：

```text
https://webarena.dev/
https://arxiv.org/abs/2307.13854
```

适合学习：

- 网页 agent benchmark 怎么定义任务。
- 环境状态和最终成功怎么验证。
- 多步网页操作为什么难。

注意：

- 网页任务强依赖环境快照。
- 真实网站数据会变，不能简单爬网页当训练数据。
- 需要记录页面 provenance 和 replay 能力。

## 5. SWE-bench

链接：

```text
https://www.swebench.com/
https://github.com/SWE-bench/SWE-bench
```

适合学习：

- 真实 GitHub issue 如何变成 coding benchmark。
- patch 通过测试作为 verifier。
- hidden tests / repository snapshot 的重要性。

注意：

- issue + patch 不等于完整 agent trajectory。
- 如果要训练 agent，需要采集 inspect/edit/test 的过程。
- 防止模型看到标准 patch 或测试答案。

## 6. Alignment Handbook 数据

链接：

```text
https://github.com/huggingface/alignment-handbook
```

适合学习：

- dataset mixer。
- SFT/DPO 数据格式。
- chat template 和训练 recipe。

注意：

- 它是 alignment 通用流程，不是专门 agent。
- 需要把 agent trajectory 转成兼容格式。

## 7. 公开数据集使用原则

```text
公开数据集用于学习格式和 baseline
私有 held-out 数据用于真实评估
业务数据必须重新做安全和隐私清洗
agent 数据必须保留 trajectory 和 verifier
```

不要把公开 benchmark 分数当成唯一能力证明。

