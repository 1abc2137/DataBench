from pathlib import Path

import streamlit as st

from core.datasets import load_csv
from core.experiment import save_experiment
from modules.error_detection.algorithm import detect_missing


ROOT = Path(__file__).resolve().parents[2]


def render() -> None:
    uploaded = st.file_uploader('上传 CSV（不超过10MB）', type=['csv'])
    path = uploaded if uploaded is not None else ROOT / 'datasets/samples/errors_demo.csv'
    try:
        df = load_csv(path)
        st.write('数据预览')
        st.dataframe(df, width='stretch')
        if st.button('运行缺失值检测示例'):
            result = detect_missing(df)
            st.success(f'检测完成：{len(result.predictions)} 个疑似缺失单元格')
            st.dataframe(result.predictions, width='stretch')
            saved = save_experiment(
                result,
                dataset_id='uploaded_csv' if uploaded else 'errors_demo_v1',
            )
            st.caption(f'实验记录已保存：{saved.name}')
    except Exception as exc:
        st.error(f'数据加载或运行失败：{exc}')
