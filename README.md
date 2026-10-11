# DataBench Starter v0.4.1

DataBench Starter 是供 8 个本科生小组并行开发的本地教学原型。v0.4.1 提供稳定接口、学生任务包、逐项测试说明以及开发自查和提交检查工具。每组在自己的模块目录中开发，不需要修改统一入口或其他小组代码。

当前只有第 1 组缺失值检测示例已经实现；第 2 至第 8 组保留独立的可打开占位页，等待各组接入算法。

## 快速开始

建议使用 Python 3.10 或 3.11。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

macOS 或 Linux 使用 `source .venv/bin/activate` 激活环境。

验收基线：测试全部通过；侧边栏显示 8 个模块；第 1 组示例返回 2 个缺失单元格并在 `experiments/` 生成 JSON；其余页面显示待实现提示且不报错。

## 目录结构

```text
DataBench_Starter/
├── app.py                    # 统一入口，只负责页面调度
├── core/
│   ├── base.py               # AlgorithmResult 合同
│   ├── acceptance.py         # 可执行验收证据合同
│   ├── datasets.py           # 单 CSV 和多 CSV 公共加载
│   ├── experiment.py         # JSON 实验记录
│   └── registry.py           # 冻结的模块清单、边界和页面入口
├── modules/
│   ├── error_detection/
│   ├── data_repair/
│   ├── quality_impact/
│   ├── dependency_discovery/
│   ├── truth_discovery/
│   ├── entity_matching/
│   ├── table_discovery/
│   └── query_analysis/
├── datasets/samples/         # 可直接运行的小型样例
├── docs/                     # 接口、模板和验证记录
└── tests/                    # 公共合同与回归测试
```

每个小组只维护 `modules/<module_id>/`。默认的页面入口是本组 `page.py` 中的 `render()`，本组 smoke test 与页面放在同一目录，因此不会与其他组争用同一个文件。详细模板见 `docs/STUDENT_MODULE_TEMPLATE.md`。

## 冻结的八个模块

| 组别 | 模块 ID | 中文名称 |
| --- | --- | --- |
| 1 | `error_detection` | 表格错误检测 |
| 2 | `data_repair` | 表格数据修复 |
| 3 | `quality_impact` | 数据质量影响 |
| 4 | `dependency_discovery` | 数据依赖发现 |
| 5 | `truth_discovery` | 多源真值发现 |
| 6 | `entity_matching` | 多源实体匹配 |
| 7 | `table_discovery` | 多源表格语义检索与关联发现 |
| 8 | `query_analysis` | SQL查询分析 |

模块 ID、中文名称、题目边界和页面入口统一保存在 `core/registry.py`，并由公共测试锁定。旧模块 ID `time_series_ad` 已废止。未经公共接口变更流程，不要修改 `core/registry.py` 或 `app.py`。

## 学生开发流程

1. 阅读 `docs/MODULE_SPEC.md` 和本组在 `core/registry.py` 中的边界。
2. 在本组目录实现算法，返回 `core.base.AlgorithmResult`。
3. 在本组 `page.py::render` 中完成数据加载、参数、运行、展示和实验保存。
4. 从本组现有 smoke test 开始，增加正常案例、非法输入、结果合同和实验保存测试。
5. 运行本组测试后，再运行 `python -m pytest -q` 检查全平台回归。
6. 提交本组目录、示例数据、依赖说明、方法说明和复现实验命令。

不要把主要算法写进 `app.py`，不要让一个模块直接依赖另一个尚未完成的模块，也不要把只服务本组的逻辑放入 `core/`。

## 可交互 Streamlit 页面要求

每组最终必须实现一个真实可交互的 Streamlit 页面。页面至少应具备：

1. 允许用户上传任务所需数据，或选择项目内置的小型示例数据。
2. 允许用户选择本组实现的方法或实验策略；最终提交应能运行至少两种方法或策略。
3. 为阈值、Top-k、随机种子、规则或其他关键参数提供合适的输入控件。
4. 由按钮触发算法真实运行，不能展示写死的结果。
5. 展示与任务匹配的预测结果、证据、指标、运行时间或对比图表。
6. 对空数据、错误格式和非法参数给出用户能够理解的错误提示。
7. 使用 `save_experiment` 保存数据集标识、方法、参数、指标、元数据和预测结果。
8. 按本组任务需要提供错误高亮、修复确认、Top-k 排序、来源可信度、执行计划树或结果下载等交互功能。

只有占位文字、静态说明、写死结果，或者只能运行单一演示按钮的页面，不算完成可交互页面。各组还应阅读 `docs/tasks/` 中本组任务书，落实对应题目的专用交互要求。

### 页面开发方法

先在本组 `algorithm.py` 中实现与 Streamlit 无关的算法函数，并返回 `AlgorithmResult`；再在 `page.py` 的 `render()` 中使用 `st.file_uploader`、`st.selectbox`、`st.slider`、`st.number_input` 等组件收集输入和参数。用户点击 `st.button` 后调用算法，通过 `st.dataframe`、`st.metric` 或图表展示结果，最后调用 `save_experiment` 保存实验记录。需要提供结果文件时，可使用 `st.download_button` 导出副本。

页面文件只负责输入、交互和展示，主要算法、指标计算和数据处理应放在本组业务文件中。可从 `docs/STUDENT_MODULE_TEMPLATE.md` 的最小页面示例开始，再结合本组任务书逐步补充方法选择、参数控件和任务专用结果展示。

## 输入输出约定

- 单个 CSV 使用 `core.datasets.load_csv`，自动增加稳定字符串行号 `__row_id`。
- 多个 CSV 使用 `core.datasets.load_csv_collection`，返回 `{table_id: DataFrame}`。
- 单文件上限 10 MB；多文件集合最多 100 个文件、已知总大小不超过 50 MB。
- 多文件可以传入 `{table_id: source}` 显式映射，也可以传入文件列表并从文件名生成稳定 `table_id`。
- 重复 `table_id` 会报错，不会静默覆盖。
- 算法结果和实验配置必须可被标准 JSON 序列化，不能直接放入 DataFrame、NumPy 对象、集合或数据库连接。

`AlgorithmResult` 必须包含 `task_type`、`algorithm` 和 `predictions`；`metrics` 与 `metadata` 必须是字典。使用 `core.experiment.save_experiment` 保存实验 JSON。

## 测试

```powershell
# 全量测试
python -m pytest -q

# 单组测试示例
python -m pytest modules\table_discovery\test_table_discovery.py -q

# 公共合同测试
python -m pytest tests -q
```

v0.4.1 的 42 个测试覆盖：模块清单与页面加载、旧 ID 排除、结果必填字段、字典字段、JSON 序列化、实验记录完整性、单文件与多文件加载、8 个 Streamlit 页面回归和验收工具。每个测试的目的和失败含义见 `docs/TESTING_GUIDE.md`。

### 开发自查与提交检查

```powershell
# 日常开发自查，可用 --module 只检查一组
python tools\acceptance.py --profile development --label weekly_check
python tools\acceptance.py --profile development --module error_detection

# 中期提交：至少一种端到端可运行方法
python tools\acceptance.py --profile midterm --module error_detection

# 最终提交：两种方法、数据集卡和完整实验说明
python tools\acceptance.py --profile final --module error_detection
```

命令会在 `reports/acceptance/` 同时生成 Markdown 和 JSON。存在未通过模块时返回非零退出码，适合用于 CI；🔎 项必须由研究生人工复核。完整约定见 `docs/ACCEPTANCE_GUIDE.md`。

## 学生开发材料

- `docs/STUDENT_RELEASE_GUIDE.md`：开发包安装、文件所有权、开发顺序和验收底线。
- `docs/tasks/README.md`：8 组任务总览及独立任务书索引。
- `docs/MINIMUM_PLAN_TEMPLATE.md`：开始复杂算法前必须提交的最小方案。
- `docs/DATASET_CARD_TEMPLATE.md`：数据来源、许可、字段、标签和预处理记录。
- `docs/SUBMISSION_CHECKLIST.md`：代码、数据、结果、页面、测试和提交自查。
- `docs/TESTING_GUIDE.md`：42 个测试逐项说明、失败含义和新增测试要求。
- `docs/ACCEPTANCE_GUIDE.md`：检查模式、自动门禁、证据入口和人工复核说明。
- `.github/ISSUE_TEMPLATE/`：运行问题、接口变更和模块阶段提交模板。

## 提交要求

- 不提交 `.venv`、缓存、实验运行 JSON、大型原始数据或敏感数据。
- 特殊依赖写明版本、用途和安装方法；不要无理由加入公共 `requirements.txt`。
- README 中的命令必须能够复制执行。
- 随机算法固定种子或把种子写入实验配置。
- 没有真值时，不报告准确率、F1、Precision@k 或 Recall@k。
- 第 8 组只使用受控测试库和只读 SQL；`EXPLAIN ANALYZE` 会真正执行查询。

