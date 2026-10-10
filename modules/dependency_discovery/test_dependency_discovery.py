from core.registry import get_module
from modules.dependency_discovery.page import render


def test_dependency_discovery_page_entrypoint():
    spec = get_module('dependency_discovery')
    assert spec.page_entrypoint == 'modules.dependency_discovery.page:render'
    assert callable(render)
