# 合成证据链演示

运行：在 online-rag-research 项目根执行 `python3 prototype/evidence_chain.py`。

全部对象、文本、引用和关系均为手工合成；没有企业数据、联网、模型调用或真实数据库操作。这里只演示明确对象起点上的证据组装和机械门控，不是完整 RAG，也不是任何论文复现。

输出：synthetic_fixture.json、demo_result.json、validation.json。结果记录包含代码与输入 hash、环境、时间、命令和检查结果。当前通过的 11 项检查仅覆盖固定合成案例，不可解释为检索效果、吞吐性能或生产安全保证。

建议查看 demo_result.json 中的 evidence 和 paths：它们分别保存原文片段以及关系的来源依据。gaps 表示分支无法读取、来源不符或预算不足。历史版本重建、关系抽取、中文召回、语义蕴含判断和真实 ACL 接入尚未实现。
