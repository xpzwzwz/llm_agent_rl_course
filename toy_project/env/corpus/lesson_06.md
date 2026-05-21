# 训练 Agent 的方法

SFT 让模型学会合法工具调用、遵守 schema、根据 observation 继续行动，并在 final 前做必要验证。训练时应该保留 assistant action 和 tool role 的边界，避免模型学习伪造 observation。

DPO 需要 preference pair，常见字段是 prompt、chosen、rejected。对 agent 来说，chosen 应该是更好的整条轨迹，rejected 可以是未验证、失败或危险的轨迹。

GRPO 适合有自动 verifier 的可验证任务。对同一个 prompt 采样多条轨迹后，可以用 reward function 给每条轨迹打分，再在组内比较哪条更好。

Reward hacking 指模型拿到高 reward，但没有真正完成任务。例如 coding agent 删除测试让 pytest 通过，或者伪造工具结果说任务已经完成。

Hidden tests 可以防止模型只针对公开测试、删除测试或绕过验证来拿分。代码任务应该保护测试文件，并用 hidden tests 检查 patch 是否真正修复问题。

