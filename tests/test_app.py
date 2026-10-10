from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.registry import MODULE_SPECS

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_app_exposes_all_registered_pages_without_exceptions():
    app = AppTest.from_file(APP).run(timeout=20)
    selector = app.sidebar.selectbox[0]

    assert selector.options == [spec.label for spec in MODULE_SPECS]
    assert len(app.exception) == 0

    for spec in MODULE_SPECS:
        selector.set_value(spec.module_id)
        app.run(timeout=20)
        assert len(app.exception) == 0
        assert app.subheader[0].value == spec.label
        selector = app.sidebar.selectbox[0]


def test_error_detection_page_keeps_runnable_example():
    app = AppTest.from_file(APP).run(timeout=20)
    assert len(app.button) == 1
    app.button[0].click().run(timeout=20)
    assert len(app.exception) == 0
    assert app.success[0].value == '检测完成：2 个疑似缺失单元格'
