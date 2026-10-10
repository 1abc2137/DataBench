from dataclasses import FrozenInstanceError

import pytest

from core.registry import MODULES, MODULE_SPECS, get_module, load_page_renderer


EXPECTED_MODULES = (
    ('error_detection', '01 表格错误检测'),
    ('data_repair', '02 表格数据修复'),
    ('quality_impact', '03 数据质量影响'),
    ('dependency_discovery', '04 数据依赖发现'),
    ('truth_discovery', '05 多源真值发现'),
    ('entity_matching', '06 多源实体匹配'),
    ('table_discovery', '07 多源表格语义检索与关联发现'),
    ('query_analysis', '08 SQL查询分析'),
)


def test_eight_modules_and_new_table_discovery():
    ids = [key for key, _ in MODULES]
    assert MODULES == EXPECTED_MODULES
    assert len(ids) == len(set(ids)) == 8
    assert 'table_discovery' in ids
    assert 'time_series_ad' not in ids
    assert any(key == 'table_discovery' and '表格' in label for key, label in MODULES)


def test_frozen_specs_have_boundaries_and_unique_pages():
    assert len(MODULE_SPECS) == 8
    assert all(spec.boundary.strip() for spec in MODULE_SPECS)
    assert len({spec.page_entrypoint for spec in MODULE_SPECS}) == 8
    with pytest.raises(FrozenInstanceError):
        MODULE_SPECS[0].module_id = 'changed'


@pytest.mark.parametrize('module_id', [module_id for module_id, _ in EXPECTED_MODULES])
def test_each_registered_page_is_importable(module_id):
    spec = get_module(module_id)
    assert spec.module_id == module_id
    assert callable(load_page_renderer(module_id))


def test_unknown_module_is_rejected():
    with pytest.raises(KeyError, match='Unknown module_id'):
        get_module('time_series_ad')
