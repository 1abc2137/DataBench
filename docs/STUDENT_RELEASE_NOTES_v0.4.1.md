# DataBench Starter v0.4.1 学生发布说明

本版本不改变已冻结的 8 个模块 ID 和 `AlgorithmResult` 字段，主要改进学生自查、测试说明和提交验收材料。

## 学生需要完成的内容

- 在本组目录增加 `acceptance.py::run_acceptance(output_dir)`。
- 提供模块 README，至少包含方法、数据、运行和限制。
- 提供正常输入、错误输入、结果合同和实验保存测试。
- 最终提交前提供至少两种方法或策略、`DATASET_CARD.md`、指标和失败案例说明。

## 自查命令

```powershell
python -m pytest -q
python tools\acceptance.py --profile development --module <module_id>
python tools\acceptance.py --profile midterm --module <module_id>
python tools\acceptance.py --profile final --module <module_id>
```

开发自查用于确认模块是否已经脱离占位状态并能用小型样例运行；中期提交检查要求至少一种端到端方法；最终提交检查要求两种方法和完整的数据、指标及失败案例说明。

当前第 1 组具有可执行示例，第 2–8 组仍是占位模块。检查全部模块时出现 `BLOCKED` 是完成度提示，不代表环境或检查工具损坏。

详细说明：

- `docs/TESTING_GUIDE.md`：42 个测试分别验证什么、失败意味着什么、学生应补哪些测试。
- `docs/ACCEPTANCE_GUIDE.md`：自动检查项、门禁判定、人工复核、报告和退出码。
