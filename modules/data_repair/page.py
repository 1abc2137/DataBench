from core.registry import get_module
from modules._page_helpers import render_placeholder


def render() -> None:
    render_placeholder(get_module('data_repair'))
