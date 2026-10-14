# DataBench 测试说明

## 1. 测试的作用和边界

当前测试套件共有 50 个测试用例，用于保护公共接口、算法注册和执行、已有示例、页面注册、数据加载和验收工具，确保一个小组的修改不会破坏其他模块。

测试全部通过只说明“现有代码符合当前合同”，不表示 8 个学生模块都已完成。未开发模块当前只有页面入口测试，完成算法后必须由对应小组补充正常输入、错误输入、结果合同、实验保存和指标测试。

运行全部测试：

```powershell
uv run python -m pytest -q
```

只运行一个文件：

```powershell
uv run python -m pytest tests\test_contract.py -q
```

只运行一个测试：

```powershell
uv run python -m pytest tests\test_contract.py::test_experiment_record -q
```

## 2. 公共测试分别检查什么

### 各模块目录中的测试：12 个

| 测试 | 数量 | 验证内容 | 失败通常表示 |
| --- | ---: | --- | --- |
| `test_<module_id>_page_entrypoint` | 8 | 注册表页面路径与本组 `render()` 一致，并且函数可调用 | 页面改名、入口路径错误或导入失败 |
| `test_normal_sample_returns_contract_result` | 1 | 错误检测默认样例能运行，返回 `error_detection` 结果并发现两个缺失单元格 | 算法输出、样例或结果合同被破坏 |
| `test_algorithm_is_registered` | 1 | 缺失值 baseline 具有合法算法清单并使用预期 runtime | 算法目录、清单或注册器被破坏 |
| `test_invalid_reserved_row_id_is_rejected` | 1 | 用户 CSV 已含保留列 `__row_id` 时必须拒绝 | 数据加载器可能覆盖内部稳定行号 |
| `test_acceptance_smoke_saves_complete_experiment` | 1 | 错误检测验收入口能运行并保存任务、算法和预测完整的 JSON | 端到端验收或实验记录断裂 |

其中 8 个页面入口用例分别覆盖：错误检测、数据修复、质量影响、依赖发现、真值发现、实体匹配、表格发现和 SQL 查询分析。

### `tests/test_acceptance.py`：4 个

| 测试 | 验证内容 | 失败通常表示 |
| --- | --- | --- |
| `test_acceptance_evidence_enforces_module_result_contract` | `AcceptanceEvidence` 接受合法证据，并拒绝结果 `task_type` 与模块 ID 不一致的情况 | 验收证据合同失效 |
| `test_development_check_distinguishes_real_thin_slice_from_placeholder` | 开发自查能把真实错误检测实现判为就绪，并把数据修复占位页判为未就绪 | 验收器把占位页误判为完成，或真实模块无法验收 |
| `test_midterm_and_final_checks_have_distinct_requirements` | 一种方法可满足中期提交检查，但不能满足最终提交所需的两种方法和完整材料 | 两种提交检查的要求没有正确区分 |
| `test_acceptance_report_is_machine_and_human_readable` | 同时生成可读 Markdown 和结构化 JSON，且汇总状态正确 | 报告格式或自动化接口被破坏 |

### `tests/test_app.py`：2 个

| 测试 | 验证内容 | 失败通常表示 |
| --- | --- | --- |
| `test_app_exposes_all_registered_pages_without_exceptions` | 使用 Streamlit 测试运行器依次打开 8 个侧边栏入口，检查标签、页面标题和异常 | 某个页面导入失败、注册丢失或页面运行抛异常 |
| `test_error_detection_page_keeps_runnable_example` | 在页面点击运行按钮，确认默认样例得到“2 个疑似缺失单元格” | 页面按钮、默认数据或错误检测示例被破坏 |

### `tests/test_algorithm_runtime.py`：7 个

| 测试方向 | 验证内容 | 失败通常表示 |
| --- | --- | --- |
| 算法发现 | `algorithm.json` 能被注册器发现，未知算法会被拒绝 | 清单路径、字段或算法 ID 错误 |
| 上传文件落盘 | 上传对象被安全保存到本次运行目录 | 子进程无法读取页面上传数据 |
| 运行证据 | 请求、结果、stdout 和 stderr 文件齐全 | executor 未形成可追踪运行记录 |
| 参数合同 | `params` 必须是字典 | 页面和算法之间的参数协议不稳定 |
| uv 命令 | 独立算法必须使用指定项目和 `--frozen` 锁文件运行 | 子进程可能使用错误环境或重新解析依赖 |
| Conda 环境 | 未准备好的 Conda 环境必须给出明确安装提示 | 页面可能直接抛出难理解的进程错误 |
| 子进程结果合同 | 缺失 `AlgorithmResult` 字段的结果 JSON 会被拒绝 | 外部算法可能绕过统一结果合同 |

### `tests/test_contract.py`：8 个

| 测试 | 数量 | 验证内容 | 失败通常表示 |
| --- | ---: | --- | --- |
| `test_csv_and_baseline` | 1 | CSV 加载后有稳定 `__row_id`，错误检测定位到两个指定单元格 | 数据加载或基础算法行为变化 |
| `test_experiment_record` | 1 | 实验 JSON 包含 ID、时间、任务、算法、数据集、配置、指标、元数据和预测 | 实验记录字段缺失或内容不一致 |
| `test_reserved_column` | 1 | 输入不能预先占用 `__row_id` | 内部行号可能被用户数据覆盖 |
| `test_algorithm_result_required_fields` | 1 | `task_type`、`algorithm`、`predictions` 必须存在且合法 | 必填字段校验被放松 |
| `test_algorithm_result_dictionary_fields` | 2 | `metrics` 和 `metadata` 必须分别是字典 | 结果结构不稳定，后续无法统一读取 |
| `test_algorithm_result_json_serialization_contract` | 1 | 合法结果可 JSON 序列化，集合等非法对象会被拒绝 | 实验可能无法保存或只能隐式转字符串 |
| `test_experiment_rejects_invalid_config` | 1 | 配置必须是字典，数据集 ID 必须是非空字符串 | 实验配置合同被破坏 |

`test_algorithm_result_dictionary_fields` 使用两个参数组合运行，因此表中 7 个测试函数对应 8 个实际用例。

### `tests/test_datasets_collection.py`：4 个

| 测试 | 验证内容 | 失败通常表示 |
| --- | --- | --- |
| `test_load_csv_collection_from_iterable` | 文件列表能生成稳定表 ID，处理中英文文件名并为每张表加入 `__row_id` | 多文件加载或 ID 规范化出错 |
| `test_load_csv_collection_accepts_explicit_ids` | 调用者可以明确指定 `left`、`right` 等表角色 | 多源任务无法稳定指定表身份 |
| `test_load_csv_collection_rejects_empty_and_duplicate_ids` | 空集合和重复表 ID 必须报错 | 输入可能被静默忽略或覆盖；此函数包含两个断言场景 |
| `test_single_path_is_not_a_collection` | 单一路径不能误当成多文件集合 | 字符串路径可能被错误地逐字符遍历 |

### `tests/test_registry.py`：11 个

| 测试 | 数量 | 验证内容 | 失败通常表示 |
| --- | ---: | --- | --- |
| `test_eight_modules_and_new_table_discovery` | 1 | 8 个模块 ID 和中文名称精确匹配，保留 `table_discovery`，排除旧 ID | 注册项被误改、遗漏或恢复旧题目 |
| `test_frozen_specs_have_boundaries_and_unique_pages` | 1 | 每个模块有边界说明、页面入口唯一，注册规格不可运行时修改 | 多组共享入口或注册数据可被意外修改 |
| `test_each_registered_page_is_importable` | 8 | 分别导入 8 个模块的页面入口 | 对应组页面路径、依赖或导入代码有问题 |
| `test_unknown_module_is_rejected` | 1 | 已废止或未知模块 ID 会明确报错 | 注册表可能静默接受错误模块 |

### `tests/test_release_materials.py`：2 个

| 测试 | 验证内容 | 失败通常表示 |
| --- | --- | --- |
| `test_student_release_materials_are_complete` | 版本号、学生指南、测试指南、数据模板、提交清单、发布说明和 8 组任务书齐全；任务书包含方法、数据、评价和边界 | 学生包缺文档或版本材料不同步 |
| `test_issue_templates_capture_required_information` | Bug 模板包含环境、复现、预期、实际和日志；接口变更模板包含兼容性与迁移方案 | 学生无法提供足够信息定位问题或变更公共接口 |

## 3. 学生新增测试的最低要求

每组完成模块时，应在 `modules/<module_id>/test_<module_id>.py` 中至少增加：

1. 正常小样例测试：已知输入得到可人工核对的输出。
2. 非法或空输入测试：明确抛出异常或返回页面错误提示。
3. 结果合同测试：`task_type`、`algorithm`、`predictions` 和 JSON 序列化正确。
4. 实验记录测试：保存后重新读取，字段与本次运行一致。
5. 指标测试：有指标时，用很小的 TP、FP、FN 或排序案例手工核对。

测试名称应能表达行为，例如：

```python
def test_rule_detector_finds_known_range_violation():
    ...

def test_rule_detector_rejects_missing_rule_configuration():
    ...
```

不要只写 `test_run()` 或只断言“没有抛异常”。

## 4. 如何理解失败信息

- `FAILED`：测试已经运行，但断言结果与预期不同。
- `ERROR`：测试准备阶段或执行阶段异常，例如导入失败、权限问题或临时目录无法创建。
- `X passed`：通过数量；参数化测试的每个参数组合分别计数。

Windows 出现 `pytest-of-用户名` 的 `PermissionError` 时，可临时使用项目内目录：

```powershell
uv run python -m pytest -q --basetemp .pytest-tmp-local
```

这只是在更换测试临时目录，不会掩盖业务测试失败。测试结束后可以删除 `.pytest-tmp-local`。

## 5. 推荐提交前命令

```powershell
# 本组测试
uv run python -m pytest modules\<module_id>\test_<module_id>.py -q

# 公共和全平台测试
uv run python -m pytest -q

# 本组开发自查
uv run python tools\acceptance.py --profile development --module <module_id>

# 根据提交要求选择更完整的检查
uv run python tools\acceptance.py --profile midterm --module <module_id>
uv run python tools\acceptance.py --profile final --module <module_id>
```
