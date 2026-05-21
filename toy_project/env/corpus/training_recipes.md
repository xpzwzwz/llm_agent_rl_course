# 训练配方摘要

SFT 数据通常来自成功 trajectory，格式可以是 messages。user 提供任务，assistant 输出 action，tool 返回环境结果，assistant 最后输出 Final。

DPO 数据格式通常包含 prompt、chosen、rejected。chosen 是更好的轨迹，rejected 是更差的轨迹。pair 构造时，验证成功的轨迹优于失败轨迹，有工具验证的轨迹优于直接猜答案。

GRPO 训练集可以只包含 prompt 和环境元数据。reward function 根据工具执行结果、测试是否通过、页面状态是否正确来返回 reward。

Rejection sampling 会对同一个任务采样多条轨迹，用 verifier 选出成功样本，再生成 SFT 和 DPO 数据。

