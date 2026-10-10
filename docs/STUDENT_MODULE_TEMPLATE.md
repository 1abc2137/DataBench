# DataBench 学生模块开发模板

## 使用范围

本模板用于实现已经注册的 8 个模块之一。学生只编辑本组的 `modules/<module_id>/`、本组示例数据和本组说明；不修改 `app.py`、其他组目录或 `core/`。

## 最小目录

```text
modules/<module_id>/
├── __init__.py
├── algorithm.py
├── acceptance.py
├── page.py
├── README.md
├── DATASET_CARD.md           # 最终验收前补齐
└── test_<module_id>.py
```

当前各组已经有 `__init__.py`、`page.py` 和 smoke test。添加 `algorithm.py` 后，把稳定公共函数从 `__init__.py` 导出。

## 可执行验收入口

在 `acceptance.py` 中提供 `run_acceptance(output_dir: Path) -> AcceptanceEvidence`。它必须使用小型本地样例真实运行方法，并将每个结果对应的实验 JSON 写入 `output_dir`：

```python
from pathlib import Path

from core.acceptance import AcceptanceEvidence
from core.experiment import save_experiment


def run_acceptance(output_dir: Path) -> AcceptanceEvidence:
    result = run_baseline(data=[])
    experiment = save_experiment(result, 'sample_v1', output_dir=output_dir)
    return AcceptanceEvidence(
        module_id='<module_id>',
        results=[result],
        experiment_files=[experiment],
        sample_files=[Path('datasets/samples/example.csv').resolve()],
    ).validate()
```

中期验收至少返回一种方法；最终验收至少返回两种不同 `algorithm` 标识的方法或实验策略。

## 最小算法示例

```python
from core.base import AlgorithmResult


def run_baseline(data, threshold=0.5):
    predictions = []
    # 在这里实现本组算法并构造基础 Python 类型结果。
    return AlgorithmResult(
        task_type='<module_id>',
        algorithm='baseline_v1',
        predictions=predictions,
        metrics={},
        metadata={'threshold': threshold},
    ).validate()
```

不要把 DataFrame、NumPy 对象、集合、模型实例或数据库连接直接放入结果。需要时转换为列表、字典、字符串、整数、浮点数、布尔值或 `None`。

## 最小页面示例

```python
import streamlit as st

from core.experiment import save_experiment
from modules.<module_id>.algorithm import run_baseline


def render() -> None:
    st.write('本组页面说明')
    if st.button('运行示例'):
        result = run_baseline(data=[])
        st.write(result.predictions)
        saved = save_experiment(
            result,
            dataset_id='sample_v1',
            config={'threshold': 0.5},
        )
        st.caption(f'实验记录已保存：{saved.name}')
```

`app.py` 会根据注册项自动调用该 `render()`，不需要增加条件分支。

## 最小测试示例

```python
from modules.<module_id>.algorithm import run_baseline


def test_baseline_contract():
    result = run_baseline(data=[])
    assert result.task_type == '<module_id>'
    assert result.algorithm
    assert result.to_dict()['predictions'] == result.predictions
```

继续增加非法输入、实验保存和指标计算测试。测试数据应足够小，默认运行不触发网络下载或长时间训练。

## 提交前检查

- 本组页面可以从统一入口打开。
- 至少一种基础方法可以运行。
- 返回 `AlgorithmResult` 且能够 JSON 序列化。
- 实验记录包含配置、指标、元数据和预测结果。
- README 说明数据来源、字段、主键、预处理、方法和限制。
- 本组测试与全量测试均通过。
- 没有修改其他组文件或未经批准的公共接口。
