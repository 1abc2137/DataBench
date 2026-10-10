# 第 7 组表格语义检索与关联发现任务书

## 目标和边界

模块 ID 为 `table_discovery`，代码目录为 `modules/table_discovery/`。系统从候选表集合中检索可能与查询表 Union 或 Join 的 Top-k 表，并保留证据。输出是候选关系，不表示已经验证可以正确合并。

## 输入和输出

- 输入：查询 CSV、多个候选 CSV、Top-k、关系类型和评分参数。
- 使用 `load_csv_collection` 给每张候选表稳定 `table_id`。
- 输出：`[{table_id,relation_type,score,evidence}]`。
- evidence 至少包含匹配列、列名分数、列值重叠或候选连接键。
- `task_type` 固定为 `table_discovery`。

## 两种基础方法

1. 列名方法：列名分词和规范化后计算 Jaccard 或编辑相似度，聚合为表级分数。
2. 列值方法：抽样计算列值重叠、Jaccard 或包含关系，并与列名分数组合。

SANTOS 和 LakeBench 用于理解语义 Union、Join 和基准设计；第一阶段不要求大模型或完整复现。

## 第一阶段数据集

- 构造 1 张查询表和至少 8 张候选表。
- 至少包含 2 张 Union 候选、2 张 Join 候选和若干干扰表。
- 提供 ground truth，记录 `query_id`、`table_id`、`relation_type` 和相关性。
- 所有文件小到能够在几秒内完成检索。

## 评价

- 有标注时报告 Precision@k、Recall@k 和可选 MRR，Union 与 Join 分开评价。
- 无标注时只展示排序、分数和证据。
- 比较单独列名、单独列值和组合分数，记录抽样和权重参数。

## 最小交付

- 两种方法均输出稳定 Top-k 和可解释 evidence。
- 页面加载查询表和多候选表，支持关系类型与 Top-k 参数。
- 测试重复文件名、无共同列、空候选集合和同分排序稳定性。

## 不做事项

- 不把 candidate union 或 candidate join 写成已验证关系。
- 不默认执行真实 Union 或 Join 并覆盖数据。
- 不沿用旧模块 ID `time_series_ad`。
