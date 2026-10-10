import streamlit as st

from core.registry import MODULE_SPECS, get_module, load_page_renderer


st.set_page_config(page_title='DataBench Starter', page_icon='🗃️', layout='wide')
st.title('DataBench · 统一算法评测平台')
st.caption('教学原型 v0.4.0：已提供阶段 3–5 自动验收门禁；仅第1组具有可运行薄片。')

module_id = st.sidebar.selectbox(
    '选择模块',
    [spec.module_id for spec in MODULE_SPECS],
    format_func=lambda value: get_module(value).label,
)
module_spec = get_module(module_id)
st.subheader(module_spec.label)
load_page_renderer(module_id)()
