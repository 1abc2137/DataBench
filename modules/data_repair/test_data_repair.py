from core.registry import get_module
from modules.data_repair.page import render


def test_data_repair_page_entrypoint():
    spec = get_module('data_repair')
    assert spec.page_entrypoint == 'modules.data_repair.page:render'
    assert callable(render)
