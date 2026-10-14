# 学生模块目录

八个小组各自维护一个与模块 ID 同名的 Python 包。公共入口通过 `core/registry.py` 中的 `page_entrypoint` 自动加载各组的 `page.py::render`，因此学生不需要修改 `app.py`。

每个目录至少保留以下结构：

```text
modules/<module_id>/
├── __init__.py
├── page.py
├── acceptance.py
├── algorithms/
│   └── <algorithm_id>/
│       ├── algorithm.json
│       └── algorithm.py
└── test_<module_id>.py
```

每种算法使用独立目录并通过 `algorithm.json` 注册。`page.py` 只负责交互和展示，通过 `core.executor.execute_algorithm` 运行算法，不直接导入算法实现或特殊依赖。轻量兼容算法使用 `builtin`，依赖冲突算法使用独立 uv 项目，uv 无法管理的系统依赖才使用 Conda。

新增代码时先让本组的 smoke test 继续通过，再补充正常案例、非法输入、输出合同和实验保存测试。需要修改模块 ID、中文名称、题目边界、`core/` 或 `app.py` 时，必须先提出公共接口变更说明。
