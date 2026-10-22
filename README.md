# 跨系统 RAG 调研与证据链原型

面向海量数据库、Confluence、既有血缘和其他业务系统的按需检索与可追溯数据理解。

背景：Confluence 基本完整保存表来源、字段语义、清洗规则和跨库解释；难点是规模与跨系统关联，不要求人工重新整理全库语义字典。目录自动定位知识，检索按问题扩展关系，回答逐结论保留来源与版本。

## 阅读顺序

1. [当前问题与范围](cross-system-retrieval.md)
2. [前沿方法比较](frontier-rag-methods.md)：Contextual Retrieval、DRIFT、LazyGraphRAG、HippoRAG 2、LightRAG、CoRAG，以及 2026 年候选 SAG、PAGE-RAG、Ψ-RAG。
3. [跨系统连接器与证据契约](connector-evidence-contract.md)
4. [数据库 + Confluence 方案](database-confluence-rag.md)：早期专题，范围以当前问题说明为准。
5. [通用在线 RAG 调研](survey.md)：保留初始背景及成果导航。

来源与阅读深度见 [frontier-sources.json](frontier-sources.json)、[database-confluence-sources.json](database-confluence-sources.json)、[sources.json](sources.json)。后续工作见 [TASK.md](TASK.md)。

## 运行合成演示

需要 Python 3.9 或以上，仅使用标准库。在仓库根目录运行：

```bash
python3 prototype/evidence_chain.py
```

演示将手工编写的 Confluence 规则、任务 SQL、血缘、队列元数据和讨论稿串成证据链，生成：

- `prototype/synthetic_fixture.json`：合成输入。
- `prototype/demo_result.json`：证据片段、关系及未完成原因。
- `prototype/validation.json`：11 项机械检查记录、环境及文件哈希。

重复运行会更新这些生成文件及运行时间。说明见 [prototype/README.md](prototype/README.md)。

## 验证范围

- 已执行：11 项固定合成案例的机械检查，包括版本、可见性、引用文本、同名隔离、预算与循环。
- 尚未执行：[12 项语义验收设计](semantic-evidence-cases.json)，包括多段共同支持、规则例外、历史生效和实际运行一致性。
- 没有模型调用、向量检索、真实企业连接器或企业数据；不是完整 RAG 服务，也不是所列论文的复现。
- 合成检查不能证明真实检索准确率、生产权限安全或企业规模性能。近期预印本的结果均不视为本项目实测。

## 研究记录

材料在 2026-10-20 至 2026-10-22 整理，按本地科研台的 deep-survey 规范由 Codex 联网调研并自审。科研台内模型未执行。本仓库保存研究成果和可复现的合成演示，不包含本机凭据、科研台会话存储或运行配置。
