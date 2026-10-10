# DataBench 阶段 3–5 验收指南

## 目标

统一验收器检查真实算法运行、结果合同、样例数据、实验 JSON、页面、README 和测试，不以“文件存在”代替端到端运行。报告中的失败项阻塞门禁，人工复核项由研究生确认后记录结论。

## 学生模块证据入口

每组在 `modules/<module_id>/acceptance.py` 提供：

```python
def run_acceptance(output_dir: Path) -> AcceptanceEvidence:
    ...
```

该函数必须：

1. 加载一个不依赖网络的小型样例。
2. 真实运行本组方法并返回一个或多个 `AlgorithmResult`。
3. 使用 `save_experiment(..., output_dir=output_dir)` 保存对应实验 JSON。
4. 返回样例路径、实验路径和结果组成的 `AcceptanceEvidence`。
5. 在普通教学机器上尽量于 10 秒内完成。

验收器在临时目录中运行证据入口，运行结束自动清理实验文件，不污染正式 `experiments/`。

## 阶段 3 周期检查

```powershell
python tools\acceptance.py --phase 3 --label week_01
python tools\acceptance.py --phase 3 --module table_discovery --label group_07
```

检查模块导入、占位页、算法文件、README、小型样例、`AlgorithmResult`、实验 JSON、运行时间、正常/错误测试和文件安全。适合每周运行并把 JSON 报告用于问题跟踪。

## 阶段 4 中期集成门禁

```powershell
python tools\acceptance.py --phase 4 --label midterm
```

在阶段 3 基础上要求每组至少一种可运行方法，并要求本组至少有正常输入、错误输入、结果合同和实验保存四类测试。只有 8 个模块和全量测试全部通过，阶段 4 门禁才通过。

## 阶段 5 最终发布门禁

```powershell
python tools\acceptance.py --phase 5 --label final
```

在阶段 4 基础上要求每组至少两种不同方法或实验策略、模块级 `DATASET_CARD.md`，以及 README 中的指标和失败案例说明。工具通过后仍需人工确认页面语义、数据许可、指标适用条件和结论是否夸大。

## 输出和退出码

- 默认输出到 `reports/acceptance/`，每次产生同名 Markdown 与 JSON。
- 所有目标模块通过且全量测试通过时退出码为 `0`。
- 存在任何自动失败项时退出码为 `1`，这是尚未满足门禁的正常信号。
- `--skip-tests` 只适合本地快速诊断，不能用于中期或最终发布决定。

## 人工复核记录

自动报告中的 🔎 项至少记录：复核人、日期、数据来源/许可、页面操作路径、指标真值条件、发现的问题和处理结论。阶段 5 不允许用口头确认替代记录。
