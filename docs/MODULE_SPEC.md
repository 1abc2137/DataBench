# DataBench 模块接口约定 v0.3

## 目的

本约定让 8 个小组能够独立开发、测试和提交模块，同时保持统一入口、结果对象和实验记录稳定。模块之间第一学期不形成运行依赖。

## 冻结的模块注册

`core/registry.py` 是模块 ID、中文名称、边界和页面入口的唯一来源。公共测试对下表进行精确检查。

| 组别 | 模块 ID | 中文名称 | 页面入口 | 题目边界 |
| --- | --- | --- | --- | --- |
| 1 | `error_detection` | 01 表格错误检测 | `modules.error_detection.page:render` | 检测并评测错误单元格，不自动修改数据。 |
| 2 | `data_repair` | 02 表格数据修复 | `modules.data_repair.page:render` | 根据已知错误位置修复，本学期不发现函数依赖。 |
| 3 | `quality_impact` | 03 数据质量影响 | `modules.quality_impact.page:render` | 评测质量问题和清洗策略对下游机器学习的影响。 |
| 4 | `dependency_discovery` | 04 数据依赖发现 | `modules.dependency_discovery.page:render` | 发现和验证函数依赖并定位违反记录，不自动修复。 |
| 5 | `truth_discovery` | 05 多源真值发现 | `modules.truth_discovery.page:render` | 从冲突声明估计真值和来源可靠性。 |
| 6 | `entity_matching` | 06 多源实体匹配 | `modules.entity_matching.page:render` | 判断记录是否对应同一实体，不承担整表检索。 |
| 7 | `table_discovery` | 07 多源表格语义检索与关联发现 | `modules.table_discovery.page:render` | 输出 Top-k Union 或 Join 候选及证据，不声称候选关系已经验证可用。 |
| 8 | `query_analysis` | 08 SQL查询分析 | `modules.query_analysis.page:render` | 在受控测试库分析只读 SQL，并明确 `EXPLAIN ANALYZE` 会执行查询。 |

学生不得直接修改 `app.py`。每组只需实现自己页面入口的 `render() -> None`。确需改变注册项时，先提交接口变更说明，再更新规范、测试和代码。

## AlgorithmResult 合同

所有算法返回 `core.base.AlgorithmResult`：

| 字段 | 要求 |
| --- | --- |
| `task_type` | 必填、非空字符串，通常等于模块 ID。 |
| `algorithm` | 必填、非空字符串，使用稳定的方法标识。 |
| `predictions` | 必填且不能为 `None`；结构由任务定义。 |
| `metrics` | 字典；只有具备对应真值时才填写相关指标。 |
| `metadata` | 字典；记录耗时、版本、种子、限制或其他上下文。 |

结果中的所有值必须可以由标准库 `json.dumps` 序列化。不要依赖 `default=str` 隐式转换未知对象。DataFrame、NumPy 标量、集合、模型对象和数据库连接应先转换成明确的基础类型。

调用 `result.validate()` 可以验证合同并返回结果本身；调用 `result.to_dict()` 可以获得经过合同检查的字典。

## 实验记录合同

使用 `core.experiment.save_experiment(result, dataset_id, config)` 保存 JSON。`dataset_id` 必须是非空字符串，`config` 必须是可序列化字典。

实验 JSON 固定包含：

```text
experiment_id
created_at
task_type
algorithm
dataset_id
config
metrics
metadata
predictions
```

第一学期不引入统一数据库。实验记录默认保存到 `experiments/`，该目录中的运行 JSON 不提交到版本库。

## 单文件输入

使用 `core.datasets.load_csv(source)`：

- 支持路径或文件对象。
- 单文件上限为 10 MB。
- CSV 至少包含一行数据。
- 输入不能已有保留字段 `__row_id`。
- 加载后在首列加入从 `0` 开始的稳定字符串 `__row_id`。

## 多文件输入

多文件是第 5、6、7 组等任务的公共需求，统一使用 `core.datasets.load_csv_collection(sources)`。

支持两种输入：

```python
# 显式 ID，推荐用于左右表、查询表和候选表角色明确的任务
tables = load_csv_collection({
    'query': query_file,
    'candidate_a': candidate_file,
})

# 文件列表，从文件名生成 ID
tables = load_csv_collection([query_file, candidate_file])
```

返回值是保持输入顺序的 `{table_id: DataFrame}`。文件列表模式会对文件名进行 Unicode 规范化、用下划线替换空格并去除不安全字符。重复 ID 会直接报错，调用者应改用显式唯一 ID。

限制：集合不能为空，最多 100 个 CSV，单文件不超过 10 MB，能够预先确定大小的文件总计不超过 50 MB。公共加载器只解决文件集合、ID、大小和稳定行号问题；查询表角色、左右表角色、Schema 对齐和任务标签仍由各组模块定义。

## 页面合同

每组页面文件导出无参数函数 `render() -> None`。统一入口负责标题、模块选择和加载页面；本组页面负责：

1. 数据输入或样例选择。
2. 参数设置与必要说明。
3. 算法运行和异常提示。
4. 与任务匹配的结果展示。
5. 调用 `save_experiment` 保存可复现实验。

主要算法应放入本组的 `algorithm.py` 或其他业务文件，而不是全部写进 `page.py`。页面导入时不应连接外部数据库、下载大型数据或自动启动耗时任务。

## 各任务 predictions 建议结构

| 模块 | 输入 | `predictions` 示例 | 建议指标 |
| --- | --- | --- | --- |
| `error_detection` | 表格和可选单元格真值 | `[{row_id,column,error_type,score}]` | cell P/R/F1 |
| `data_repair` | 表格、指定错误位置和可选干净真值 | `[{row_id,column,old_value,new_value}]` | 修复值准确率、repair P/R/F1 |
| `quality_impact` | 表格、扰动配置和分类任务 | `{quality_metrics:{},downstream_metrics:{}}` | 质量变化、分类 F1 变化 |
| `dependency_discovery` | 表格 | `[{lhs:[...],rhs:'...',violations:[...]}]` | FD 数量、违反数、耗时 |
| `truth_discovery` | 多源长表 | `[{object_id,attribute,truth_value,confidence}]` | truth accuracy |
| `entity_matching` | 左右表和候选对 | `[{left_id,right_id,score,is_match}]` | pair P/R/F1 |
| `table_discovery` | 查询表和候选表集合 | `[{table_id,relation_type,score,evidence}]` | 有标注时使用 Recall@k、Precision@k |
| `query_analysis` | 只读 SQL 和测试库连接配置 | `{plan:{},execution_time_ms:...,diagnostics:{}}` | 耗时、行数估计误差 |

不同任务不强行使用同一种预测结构或通用分类 F1。每组必须在自己的说明中补充字段、主键、示例、指标公式和适用条件。

## 测试要求

每组目录已经包含一个不会与其他组冲突的 smoke test。开发时至少增加：

- 一个正常小样例。
- 一个空数据或非法输入案例。
- 一个 `AlgorithmResult` 输出合同案例。
- 一个实验 JSON 保存案例。
- 如有评价指标，增加一个可以手工验证的计算案例。

提交前运行本组测试和全量测试。公共测试会检查注册项精确值、8 个页面可加载、旧 ID 不存在、结果与实验记录可序列化，以及多文件输入约定。

## 公共接口变更流程

1. 写明当前接口、期望接口、变更理由和受影响模块。
2. 判断需求是否至少被多个模块复用；仅服务单组的逻辑留在组内。
3. 先更新规范和测试，再修改公共实现。
4. 提供兼容层或迁移说明。
5. 合并前后运行全量测试和受影响模块示例。
6. 更新版本号与变更记录，并通知所有小组。
