# DataBench 学生模块开发模板

## 使用范围

本模板用于实现已经注册的 8 个模块之一。学生只编辑本组的 `modules/<module_id>/`、本组示例数据和本组说明；不修改 `app.py`、其他组目录或 `core/`。

## 最小目录

```text
modules/<module_id>/
├── __init__.py
├── acceptance.py
├── page.py
├── README.md
├── DATASET_CARD.md
├── test_<module_id>.py
└── algorithms/
    └── <algorithm_id>/
        ├── __init__.py
        ├── algorithm.json
        └── algorithm.py
```

每种算法使用独立目录和唯一 `algorithm_id`。不要再在模块根目录创建统一的 `algorithm.py`，页面也不要直接导入算法函数。

## 选择运行环境

### builtin

算法只使用根 `pyproject.toml` 已有的公共依赖时使用。`algorithm.json` 示例：

```json
{
  "module_id": "<module_id>",
  "algorithm_id": "baseline_v1",
  "label": "Baseline V1",
  "runtime": "builtin",
  "entrypoint": "modules.<module_id>.algorithms.baseline_v1.algorithm:run",
  "timeout_seconds": 60
}
```

`algorithm.py` 统一接收 `inputs` 和 `params`：

```python
from core.base import AlgorithmResult


def run(inputs, params):
    dataset_path = inputs['dataset_path']
    threshold = float(params.get('threshold', 0.5))
    predictions = []
    return AlgorithmResult(
        task_type='<module_id>',
        algorithm='baseline_v1',
        predictions=predictions,
        metrics={},
        metadata={'threshold': threshold},
    ).validate()
```

### 独立 uv 环境

算法需要不同 Python 或冲突依赖时，在算法目录增加 `pyproject.toml`、`uv.lock`、`.python-version` 和 `runner.py`。清单使用 `runtime: "uv"`，`project_dir` 是相对仓库根目录的路径，`entrypoint` 是相对算法项目目录的脚本。

在算法目录初始化时必须使用独立项目，不能加入根 workspace：

```powershell
uv init --no-workspace --python 3.10
uv add <算法依赖>
uv lock
```

`runner.py` 读取命令行中的 `request.json` 和 `result.json` 路径，返回包含 `task_type`、`algorithm`、`predictions`、`metrics`、`metadata` 的 JSON 对象。子进程不需要导入公共 `core`，父进程会再次验证结果合同。可以直接复制 `docs/ALGORITHM_RUNNER_TEMPLATE.py` 作为起点。

### Conda 环境

只有 uv 无法管理 CUDA、系统库或 Conda 专用依赖时才使用。提交 `environment.yml`，并在清单中设置 `runtime: "conda"`、`project_dir` 和 `environment_file`。不要同时用 uv 和 Conda 管理同一算法环境。

## 页面调用

```python
import streamlit as st

from core.algorithm_registry import list_algorithms
from core.executor import execute_algorithm
from core.experiment import save_experiment


def render() -> None:
    algorithms = list_algorithms('<module_id>')
    labels = {item.algorithm_id: item.label for item in algorithms}
    algorithm_id = st.selectbox(
        '选择算法',
        [item.algorithm_id for item in algorithms],
        format_func=labels.get,
    )
    uploaded = st.file_uploader('上传数据')
    if st.button('运行') and uploaded is not None:
        result = execute_algorithm(
            module_id='<module_id>',
            algorithm_id=algorithm_id,
            inputs={'dataset_path': uploaded},
            params={'threshold': 0.5},
        )
        st.write(result.predictions)
        saved = save_experiment(
            result,
            dataset_id='uploaded_data',
            config={'algorithm_id': algorithm_id, 'threshold': 0.5},
        )
        st.caption(f'实验记录已保存：{saved.name}')
```

上传对象会由公共执行器保存到本次运行目录，算法收到的是本地文件路径。

## 可执行验收入口

```python
from pathlib import Path

from core.acceptance import AcceptanceEvidence
from core.executor import execute_algorithm
from core.experiment import save_experiment


def run_acceptance(output_dir: Path) -> AcceptanceEvidence:
    sample = Path('datasets/samples/example.csv').resolve()
    result = execute_algorithm(
        '<module_id>',
        'baseline_v1',
        {'dataset_path': sample},
        params={},
        workspace_root=output_dir / 'runs',
    )
    experiment = save_experiment(result, 'sample_v1', output_dir=output_dir)
    return AcceptanceEvidence(
        module_id='<module_id>',
        results=[result],
        experiment_files=[experiment],
        sample_files=[sample],
    ).validate()
```

## 测试示例

```python
from core.executor import execute_algorithm


def test_baseline_contract(tmp_path):
    result = execute_algorithm(
        '<module_id>',
        'baseline_v1',
        {'dataset_path': 'datasets/samples/example.csv'},
        workspace_root=tmp_path,
    )
    assert result.task_type == '<module_id>'
    assert result.algorithm == 'baseline_v1'
    assert result.to_dict()['predictions'] == result.predictions
```

测试数据必须足够小，默认运行不得触发网络下载或长时间训练。公共测试不负责安装所有特殊算法环境；独立算法应在自己的 uv 或 Conda 环境中补充真实运行测试。

## 常用命令

```powershell
uv run python tools\algorithm_env.py list
uv run python tools\algorithm_env.py sync <module_id> <algorithm_id>
uv run python tools\algorithm_env.py check <module_id> <algorithm_id>
uv run python -m pytest modules\<module_id>\test_<module_id>.py -q
uv run python -m pytest -q
```

## 提交前检查

- 页面可以从统一入口打开。
- 至少一种注册算法可以真实运行。
- 页面只通过 `execute_algorithm` 调用算法。
- 返回结果满足 `AlgorithmResult` 并能被 JSON 序列化。
- 每个独立 uv 算法提交 `pyproject.toml`、`uv.lock` 和 `.python-version`。
- 实验记录包含配置、指标、元数据和预测结果。
- README 说明论文、代码来源、数据、环境、方法和限制。
- 没有提交 `.venv`、`.algorithm_envs`、`runs` 或模型缓存。
