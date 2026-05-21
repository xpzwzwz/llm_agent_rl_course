# 数据许可和治理 FAQ

这份文档不是法律意见，而是数据构造团队需要和法务、合规、安全一起确认的问题清单。

## 1. GitHub 代码能不能直接拿来训练？

不能只看“公开可见”。还要看：

- 仓库许可证。
- 是否允许商业使用。
- 是否允许衍生作品。
- 是否包含第三方代码。
- 是否包含 secret 或个人信息。

建议：

- 保存 repo URL、commit、license。
- 只使用允许用途的数据。
- 训练前做 secret scan。
- 对生成 patch 评估版权和相似度风险。

## 2. 网页数据能不能训练？

要看：

- 网站条款。
- robots / 使用政策。
- 数据是否个人信息。
- 是否高风险领域。

网页 agent 数据通常更适合保存任务轨迹和摘要，而不是无差别保存全文。

## 3. 用户数据如何授权？

每条用户来源数据要能追踪：

```text
user_consent_status
consent_version
collection_time
allowed_use
retention_policy
deletion_request_status
```

没有授权的数据不要进入训练池。

## 4. 用户删除请求如何传播？

需要 dataset lineage：

```text
raw log -> trajectory -> SFT/DPO/RL dataset -> model training run
```

收到删除请求后要能回答：

- 哪些 raw log 包含该用户数据？
- 哪些训练样本派生自它？
- 哪些模型版本使用过？
- 是否需要重训或风险评估？

## 5. 脱敏后就安全吗？

不一定。

风险：

- 多字段组合重新识别。
- 内部 URL 暴露业务结构。
- 错误栈暴露路径和用户名。
- 对话上下文仍可识别个人。

脱敏要结合人工抽查和自动扫描。

## 6. Dataset Lineage 必须记录什么？

```text
source_id
source_type
license
consent_status
raw_data_version
redaction_version
transform_script_version
dataset_version
training_run_id
```

没有 lineage 的数据不应进入生产训练。

## 7. 数据保留多久？

按风险分层：

```text
raw user logs: 最短
redacted trajectories: 中等
dataset cards / metrics: 长期
regression cases: 长期，但要脱敏
```

保留周期应由合规和业务共同确定。

