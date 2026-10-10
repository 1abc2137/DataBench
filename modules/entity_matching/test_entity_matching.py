from core.registry import get_module
from modules.entity_matching.page import render


def test_entity_matching_page_entrypoint():
    spec = get_module('entity_matching')
    assert spec.page_entrypoint == 'modules.entity_matching.page:render'
    assert callable(render)
