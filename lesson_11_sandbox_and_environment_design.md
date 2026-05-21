# 第十一课：Sandbox 和环境设计

## 1. 为什么需要 Sandbox

Agent RL 必须让模型和环境交互。没有 sandbox，就会有三类问题：

- 不安全：模型可能删除文件、发请求、泄露密钥。
- 不可复现：同一任务今天能过，明天页面变了。
- 不可验证：不知道任务到底完成没完成。

Sandbox 的目标是给 agent 一个受控世界：

```text
可执行工具 + 固定初始状态 + 可记录日志 + 自动验证 + 可重置
```

## 2. Coding Sandbox

代码任务推荐 Docker 或轻量容器。

每个任务需要：

```json
{
  "task_id": "github_fix_0001",
  "base_image": "python:3.11",
  "repo_snapshot": "parser_repo_v1.tar.gz",
  "setup_command": "pip install -e .",
  "test_command": "pytest tests/test_parser.py -q",
  "hidden_test_command": "pytest hidden_tests -q",
  "max_steps": 30,
  "write_allowlist": ["src/", "tests/"]
}
```

工具边界：

- `read_file` 只能读仓库目录。
- `edit_file` 只能改 allowlist。
- `run_tests` 只能运行允许命令。
- 禁止网络，除非任务明确需要。
- 禁止删除测试或修改 CI 配置，除非任务要求。

## 3. Browser Sandbox

网页任务推荐 Playwright 或专门的网页环境。

需要固定：

- 初始 URL。
- 登录态。
- 后端数据库 seed。
- 页面版本。
- 最大步骤数。
- 禁止危险动作列表。

任务定义：

```json
{
  "task_id": "web_order_0001",
  "start_url": "https://shop.local/orders",
  "goal": "找到订单 #123 的物流状态。",
  "success_check": {
    "type": "dom_text",
    "selector": "#shipping-status",
    "expected": "已发货"
  },
  "max_steps": 15
}
```

浏览器 observation 可以包含：

- URL。
- 页面标题。
- 可访问性树。
- 关键 DOM 文本。
- 截图引用。
- 当前焦点元素。

不要把完整 DOM 无脑塞给模型，噪声太大。

## 4. API Sandbox

API agent 适合 mock server。

Mock server 要提供：

- 固定数据 seed。
- 请求日志。
- schema 校验。
- 错误注入。
- 最终状态检查。

例如：

```json
{
  "task": "把用户 u123 的套餐升级到 pro。",
  "allowed_apis": ["get_user", "update_plan", "get_invoice"],
  "success_check": "db.users.u123.plan == 'pro'"
}
```

这样 reward 不依赖模型自述，而依赖数据库状态。

## 5. 文件系统 Sandbox

文件任务看似简单，也要隔离：

- 每个任务一个临时目录。
- 只允许读写任务目录。
- 禁止访问 `$HOME/.ssh`、环境变量、系统配置。
- 所有写操作记录 patch。
- 任务结束后销毁目录。

## 6. 环境 Reset

RL 会反复采样同一任务，所以 reset 必须可靠：

```text
reset(task_id)
  -> 清空临时目录
  -> 恢复 repo/browser/db snapshot
  -> 重置日志
  -> 返回初始 observation
```

如果 reset 不可靠，模型可能利用上一次运行留下的状态拿奖励。

## 7. 日志和回放

每次执行都要能回放：

```text
task_id
environment_version
model_checkpoint
random_seed
step logs
tool stdout/stderr
final verifier result
```

回放能力用于：

- debug reward hacking。
- 构造 SFT/DPO 数据。
- 比较模型版本。
- 人工审查高分轨迹。

## 8. 安全边界

危险工具必须默认关闭：

- 真实付款。
- 发送邮件。
- 删除生产数据。
- 访问外网。
- 修改系统文件。
- 读取密钥。

如果业务必须用危险工具，先做两阶段执行：

```text
agent propose action -> policy checker -> human or rule approval -> execute
```

训练环境也要模拟这个审批流程，否则模型上线后会不适应。

