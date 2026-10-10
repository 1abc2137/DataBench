# DataBench Starter v0.4.0 学生发布说明

本版本增加阶段 3–5 的统一验收基础设施，不改变已冻结的 8 个模块 ID 和 `AlgorithmResult` 字段。

## 学生需要新增的内容

- 在本组目录增加 `acceptance.py::run_acceptance(output_dir)`。
- 提供模块 README，至少包含方法、数据、运行和限制。
- 中期前提供正常、错误、合同和实验保存测试。
- 最终验收前提供至少两种方法或策略、`DATASET_CARD.md`、指标和失败案例说明。

## 自查命令

```powershell
python tools\acceptance.py --phase 3 --module <module_id>
python -m pytest -q
```

当前第 1 组具有可执行薄片；第 2–8 组仍会被门禁标记为 `BLOCKED`，直到各组接入实际实现。
