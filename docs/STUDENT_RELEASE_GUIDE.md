# DataBench Starter 学生开发包使用说明

## 发布信息

学生开发包版本为 v0.5.0。压缩包名称为 `DataBench_Starter_v0.5.0_student.zip`，对应 SHA-256 文件与压缩包放在同一 `release` 目录。解压后先核对版本文件，再安装依赖和运行测试。

## 开始前必须完成

1. 阅读根目录 README、`docs/MODULE_SPEC.md` 和本组任务书。
2. 使用 `docs/MINIMUM_PLAN_TEMPLATE.md` 写清输入、输出、两种基础方法、评价方式和第一阶段数据集。
3. 使用 `docs/DATASET_CARD_TEMPLATE.md` 记录数据来源、许可、字段、主键、标签和预处理。
4. 先提交小型样例与最小可运行方案，通过确认后再引入复杂模型或大型数据。

## 安装和验证

```powershell
uv sync --frozen
uv run python -m pytest -q
uv run python -m streamlit run app.py
```

先安装 uv；项目会根据 `.python-version` 自动准备 Python 3.10，不要手工创建或激活虚拟环境。首次验收应看到 50 项测试通过；第 1 组示例检测到 2 个缺失单元格；第 2 至第 8 组占位页可以打开。

## 文件所有权

- 每组只修改 `modules/<module_id>/`、本组样例数据和本组说明。
- 不直接修改 `app.py`、`core/registry.py`、公共测试或其他组目录。
- 只有多个小组真正需要的能力才进入 `core/`。
- 公共接口变更先使用接口变更 Issue 模板讨论，通过后再实现。

## 开发顺序

1. 保持本组现有 smoke test 通过。
2. 创建可以在几秒内运行的小型示例数据。
3. 在 `algorithms/<algorithm_id>/` 完成第一种简单基线、`algorithm.json` 和 `AlgorithmResult` 输出。
4. 在本组页面通过 `execute_algorithm` 显示输入、参数、结果和错误提示。
5. 使用 `save_experiment` 保存 JSON。
6. 增加第二种方法或实验策略及对比指标。
7. 增加正常、异常、合同、实验保存和指标测试。
8. 按 `docs/SUBMISSION_CHECKLIST.md` 自查后提交。

每组还需提供 `acceptance.py::run_acceptance(output_dir)`，用小型样例真实运行算法并返回 `AcceptanceEvidence`。可随时运行 `uv run python tools\acceptance.py --profile development --module <module_id>` 查看本组缺失项。

`docs/TESTING_GUIDE.md` 逐项解释公共测试；`docs/ACCEPTANCE_GUIDE.md` 解释自动检查项、门禁判定和人工复核。开始开发前应先读这两份说明，避免把“测试通过”误解为“模块已经完成”。

## 问题反馈

普通运行问题使用 Bug 报告模板，必须包含环境、复现步骤、预期结果、实际结果和完整日志。公共接口需求使用接口变更模板，说明受影响模块、兼容性和迁移方案。不要只发送截图或“运行不了”。

## 验收底线

- README 中的命令可以直接复制执行。
- 模块能从统一入口打开，并能独立运行小型示例。
- 返回结果和实验记录能够标准 JSON 序列化。
- 数据来源和许可清楚，不包含敏感数据。
- 没有真值时不报告需要真值的指标。
- 本组测试和全量测试均通过。
