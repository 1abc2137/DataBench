# DataBench Starter v0.5.0 学生发布说明

本版本不改变冻结的 8 个模块 ID 和 `AlgorithmResult` 五个字段，环境与算法调用方式改为 uv 管理和统一 executor。

## 必须使用的新命令

```powershell
uv sync --frozen
uv run python -m pytest -q
uv run python -m streamlit run app.py
```

项目不再提供 `requirements.txt`，也不要求学生手工创建或激活 `.venv`。

## 算法目录

每种算法放在：

```text
modules/<module_id>/algorithms/<algorithm_id>/
```

每个算法必须提供 `algorithm.json`。轻量兼容算法使用 `builtin`；依赖冲突算法使用独立 uv 项目；只有 uv 无法管理的系统依赖才使用 Conda。页面统一通过 `core.executor.execute_algorithm` 调用，不直接导入特殊算法包。

## 环境命令

```powershell
uv run python tools\algorithm_env.py list
uv run python tools\algorithm_env.py sync <module_id> <algorithm_id>
uv run python tools\algorithm_env.py check <module_id> <algorithm_id>
```

## 验收命令

```powershell
uv run python tools\acceptance.py --profile development --module <module_id>
uv run python tools\acceptance.py --profile midterm --module <module_id>
uv run python tools\acceptance.py --profile final --module <module_id>
```

当前第 1 组具有通过新 executor 运行的缺失值示例，第 2–8 组仍是占位模块。检查全部模块时出现 `BLOCKED` 是完成度提示，不代表环境或检查工具损坏。
