from core.registry import get_module
from modules.quality_impact.page import render


def test_quality_impact_page_entrypoint():
    spec = get_module('quality_impact')
    assert spec.page_entrypoint == 'modules.quality_impact.page:render'
    assert callable(render)
