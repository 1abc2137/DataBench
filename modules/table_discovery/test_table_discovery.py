from core.registry import get_module
from modules.table_discovery.page import render


def test_table_discovery_page_entrypoint():
    spec = get_module('table_discovery')
    assert spec.page_entrypoint == 'modules.table_discovery.page:render'
    assert callable(render)
