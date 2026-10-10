from core.registry import get_module
from modules.query_analysis.page import render


def test_query_analysis_page_entrypoint():
    spec = get_module('query_analysis')
    assert spec.page_entrypoint == 'modules.query_analysis.page:render'
    assert callable(render)
