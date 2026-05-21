# 多模态 / VLM Agent 数据 FAQ

## 1. 图像 token 要不要算 loss？

通常不要。图像是输入，不是语言目标。

训练时要确认：

- 图像 special tokens 不作为 label。
- assistant 文本才算 loss。
- tool/action 文本格式稳定。

## 2. Screenshot、DOM、Accessibility Tree 怎么保存？

建议同时保存三类引用：

```text
screenshot_ref
dom_snapshot_ref
accessibility_tree
```

模型可见内容可以是精简 observation，原始截图和 DOM 作为审计与回放材料。

## 3. VLM Agent 的 Action 怎么标？

常见 action：

```json
{"action":"click","arguments":{"x":421,"y":233}}
{"action":"click_element","arguments":{"label":"提交订单"}}
{"action":"type","arguments":{"selector":"#search","text":"123"}}
```

优先使用语义元素 action。纯坐标 action 对分辨率和页面变化很敏感。

## 4. 图像和工具结果怎么对齐？

每一步都要有：

```text
image_frame_id
observation_text
action
tool_result
timestamp
```

不要让截图和 action 顺序错位。错位数据对 VLM agent 伤害很大。

## 5. VLM DPO Pair 怎么构造？

同一视觉状态、同一任务下比较两条轨迹：

```text
正确点击目标元素 > 点击相似但错误元素
读取页面状态后提交 > 盲目提交
识别弹窗风险 > 忽略弹窗继续
```

chosen/rejected 应共享同一初始视觉 observation。

## 6. 多模态数据常见坏味道

- 截图缺失。
- OCR 文本和截图不一致。
- 坐标基于不同分辨率。
- action 指向不可见元素。
- 图片中含个人信息未脱敏。
- 截图来自 final 后，而 action 发生在 final 前。

