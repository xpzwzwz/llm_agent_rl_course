# 长上下文数据 FAQ

## 1. 长上下文数据最大风险是什么？

模型看到了很多 token，但训练信号可能很少。

风险：

- 有效信息被稀释。
- 截断丢关键证据。
- 模型学会复制长文。
- eval 泄漏更难发现。

## 2. Document chunk provenance 怎么记录？

每个 chunk 记录：

```text
doc_id
chunk_id
source_uri
start_offset
end_offset
created_at
retrieval_query
```

没有 provenance 的 chunk 不适合用于可审计训练。

## 3. Summary memory 能不能进训练？

可以，但要标明是模型生成还是人工生成。

风险：

- summary 丢失关键事实。
- summary 引入幻觉。
- 后续模型把 summary 当原始事实。

处理：

- 保留 raw_ref。
- 对关键任务不要只保留 summary。
- summary 进入训练前抽查。

## 4. 长上下文 DPO 怎么构造？

同一个长上下文下比较：

```text
引用正确段落的回答 > 找错段落的回答
承认上下文无答案 > 编造答案
完整覆盖多个证据 > 只看开头
```

要检查 chosen/rejected 是否都能看到同样上下文。

## 5. Context packing 有什么坑？

多个文档打包时要保留边界：

```text
<doc id="A">...</doc>
<doc id="B">...</doc>
```

否则模型可能混淆来源。

## 6. 长上下文 eval 泄漏怎么查？

检查：

- train/eval doc_id overlap。
- near-duplicate chunks。
- 同一网页不同抓取时间。
- 同一 GitHub issue 的 comment/patch。

长上下文去重不能只按全文 hash。

