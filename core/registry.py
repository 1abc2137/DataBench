from dataclasses import dataclass
from importlib import import_module
from typing import Callable


@dataclass(frozen=True)
class ModuleSpec:
    module_id: str
    label: str
    boundary: str
    page_entrypoint: str

    def load_page(self) -> Callable[[], None]:
        module_name, function_name = self.page_entrypoint.split(':', maxsplit=1)
        renderer = getattr(import_module(module_name), function_name)
        if not callable(renderer):
            raise TypeError(f'Page entrypoint is not callable: {self.page_entrypoint}')
        return renderer


MODULE_SPECS = (
    ModuleSpec(
        'error_detection',
        '01 表格错误检测',
        '检测并评测表格中的错误单元格；不负责自动修改数据。',
        'modules.error_detection.page:render',
    ),
    ModuleSpec(
        'data_repair',
        '02 表格数据修复',
        '根据已知或人工指定的错误位置生成修复建议；本学期不发现函数依赖。',
        'modules.data_repair.page:render',
    ),
    ModuleSpec(
        'quality_impact',
        '03 数据质量影响',
        '评测数据质量问题与清洗策略对下游机器学习任务的影响。',
        'modules.quality_impact.page:render',
    ),
    ModuleSpec(
        'dependency_discovery',
        '04 数据依赖发现',
        '发现和验证函数依赖并定位违反记录；本学期不自动修复单元格。',
        'modules.dependency_discovery.page:render',
    ),
    ModuleSpec(
        'truth_discovery',
        '05 多源真值发现',
        '从多个信息源的冲突声明中估计真值与来源可靠性。',
        'modules.truth_discovery.page:render',
    ),
    ModuleSpec(
        'entity_matching',
        '06 多源实体匹配',
        '判断不同数据源中的记录是否指向同一实体；不承担整表检索。',
        'modules.entity_matching.page:render',
    ),
    ModuleSpec(
        'table_discovery',
        '07 多源表格语义检索与关联发现',
        '输出 Top-k Union 或 Join 候选及证据；候选关系不等同于已验证可用关系。',
        'modules.table_discovery.page:render',
    ),
    ModuleSpec(
        'query_analysis',
        '08 SQL查询分析',
        '仅在受控测试库分析只读 SQL；EXPLAIN ANALYZE 会实际执行查询。',
        'modules.query_analysis.page:render',
    ),
)

_MODULE_BY_ID = {spec.module_id: spec for spec in MODULE_SPECS}
if len(_MODULE_BY_ID) != len(MODULE_SPECS):
    raise RuntimeError('Duplicate module_id in MODULE_SPECS')

# v0.2 compatibility: consumers that only need (id, label) can keep using MODULES.
MODULES = tuple((spec.module_id, spec.label) for spec in MODULE_SPECS)


def get_module(module_id: str) -> ModuleSpec:
    try:
        return _MODULE_BY_ID[module_id]
    except KeyError as exc:
        raise KeyError(f'Unknown module_id: {module_id}') from exc


def load_page_renderer(module_id: str) -> Callable[[], None]:
    return get_module(module_id).load_page()
