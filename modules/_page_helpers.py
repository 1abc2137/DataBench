import streamlit as st

from core.registry import ModuleSpec


def render_placeholder(spec: ModuleSpec) -> None:
    st.info('本模块尚未实现。请在本组目录中接入算法与页面。')
    st.write('建议流程：数据加载 → 参数设置 → 算法运行 → 结果展示 → 实验保存。')
    st.caption(f'题目边界：{spec.boundary}')
