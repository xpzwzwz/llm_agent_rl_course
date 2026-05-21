# 业务域数据构造配方

不同 agent 场景的数据构造重点不同。本页给出常见业务域的配方。

## 1. Coding Agent

核心数据：

- issue 描述。
- repo snapshot。
- inspect/edit/test trajectory。
- visible tests 和 hidden tests。
- patch diff。

好 SFT：

```text
复现失败 -> 搜索代码 -> 修改最小 patch -> 运行测试 -> final
```

好 DPO pair：

```text
hidden tests 通过 patch > 只通过 visible tests patch
运行测试轨迹 > 直接猜修复建议
最小 patch > 大范围无关改动
```

特殊风险：

- 删除测试。
- 修改配置跳过测试。
- 训练集泄漏标准 patch。

## 2. Browser Agent

核心数据：

- 任务目标。
- 初始 URL。
- 页面 observation。
- click/type/select action。
- 最终页面或数据库状态。

好 SFT：

```text
读取页面 -> 找控件 -> 填表 -> 提交 -> 检查最终状态
```

好 DPO pair：

```text
正确提交并验证 > 到达页面但没提交
识别 prompt injection > 执行网页恶意指令
少量有效点击 > 重复乱点
```

特殊风险：

- 网页内容变化。
- prompt injection。
- 误提交真实操作。

## 3. API / Workflow Agent

核心数据：

- API schema。
- 权限边界。
- mock server 状态。
- 调用链。
- 最终数据库状态。

好 DPO pair：

```text
先 get_user 再 update_plan > 直接盲改
修改正确用户 > 修改错误用户
dry-run 后确认 > 直接危险执行
```

特殊风险：

- 参数注入。
- 越权调用。
- 状态不可回滚。

## 4. Customer Support Agent

核心数据：

- 用户问题。
- 订单/账户状态。
- 公司政策。
- 回复草稿。
- 是否解决问题。

好 DPO pair：

```text
基于政策和账户状态回答 > 编造政策
明确升级人工 > 乱承诺退款
保护隐私 > 泄露账户信息
```

特殊风险：

- 幻觉政策。
- 过度拒绝。
- 隐私泄露。
- 情绪安抚和事实正确冲突。

## 5. Data Analysis Agent

核心数据：

- 数据集 schema。
- 分析问题。
- SQL/Python action。
- 中间结果。
- 图表/结论。

好 DPO pair：

```text
检查 schema 后写 SQL > 猜字段名
验证聚合口径 > 直接下结论
说明限制 > 夸大结论
```

特殊风险：

- 数据泄漏。
- 统计口径错误。
- 图表误导。
- SQL 注入。

## 6. 每个域都要写 Domain Card

```text
domain_name
allowed_tools
dangerous_tools
success_verifier
hidden_checks
privacy_policy
common_failure_types
must_have_sft_patterns
must_have_dpo_pairs
blocked_data
```

没有 domain card，就不要大规模采集该域数据。

