from core.registry import get_module
from modules.truth_discovery.page import render


def test_truth_discovery_page_entrypoint():
    spec = get_module('truth_discovery')
    assert spec.page_entrypoint == 'modules.truth_discovery.page:render'
    assert callable(render)
