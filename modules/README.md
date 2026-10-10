# 学生模块目录

八个小组各自维护一个与模块 ID 同名的 Python 包。公共入口通过 `core/registry.py` 中的 `page_entrypoint` 自动加载各组的 `page.py::render`，因此学生不需要修改 `app.py`。

每个目录至少保留以下结构：

```text
modules/<module_id>/
├── __init__.py
├── page.py
└── test_<module_id>.py
```

建议将算法实现放在同目录的 `algorithm.py` 或更细分的文件中，并由 `__init__.py` 导出稳定的公共函数。`page.py` 只负责交互和展示，不应把主要算法全部写在页面文件里。

新增代码时先让本组的 smoke test 继续通过，再补充正常案例、非法输入、输出合同和实验保存测试。需要修改模块 ID、中文名称、题目边界、`core/` 或 `app.py` 时，必须先提出公共接口变更说明。
