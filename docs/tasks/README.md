# DataBench 八组任务说明总览

每组先完成本组任务书中的最小端到端薄片，再扩展复杂算法。第一阶段优先使用本组自建的小型、可人工核对数据，避免下载和环境问题掩盖接口问题。

| 组别 | 模块 ID | 第一种方法 | 第二种方法或策略 | 主要评价 |
| --- | --- | --- | --- | --- |
| 1 | `error_detection` | 缺失、类型和领域规则 | IQR 或稳健 Z 分数异常检测 | cell P/R/F1 |
| 2 | `data_repair` | 众数或频率修复 | 相似记录或 kNN 修复 | 修复准确率、repair P/R/F1 |
| 3 | `quality_impact` | 删除或常量填充策略 | 统计插补和去重策略 | 质量变化、下游 F1 变化 |
| 4 | `dependency_discovery` | 小规模穷举验证 | TANE 风格层次搜索与剪枝 | FD P/R、违反数、耗时 |
| 5 | `truth_discovery` | 多数投票 | 迭代来源加权投票 | truth accuracy、来源可靠性 |
| 6 | `entity_matching` | 规范化精确和字符串规则 | Fellegi-Sunter 或逻辑回归 | pair P/R/F1 |
| 7 | `table_discovery` | 列名 Jaccard | 列值重叠和组合评分 | Precision@k、Recall@k、证据 |
| 8 | `query_analysis` | 默认执行计划基线 | 索引或受控优化器设置对比 | 耗时、估计误差、计划差异 |

统一要求：返回 `AlgorithmResult`、保存实验 JSON、提供数据卡、至少一个正常和一个错误输入测试、不得依赖其他未完成模块。

各组任务书：

- `01_error_detection.md`
- `02_data_repair.md`
- `03_quality_impact.md`
- `04_dependency_discovery.md`
- `05_truth_discovery.md`
- `06_entity_matching.md`
- `07_table_discovery.md`
- `08_query_analysis.md`
