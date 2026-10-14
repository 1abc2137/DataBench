from pathlib import Path

import streamlit as st

from core.algorithm_registry import list_algorithms
from core.datasets import load_csv
from core.executor import execute_algorithm
from core.experiment import save_experiment
from core.runtime_errors import AlgorithmRuntimeError


ROOT = Path(__file__).resolve().parents[2]


def render() -> None:
    uploaded = st.file_uploader('上传 CSV（不超过10MB）', type=['csv'])
    path = uploaded if uploaded is not None else ROOT / 'datasets/samples/errors_demo.csv'
    try:
        df = load_csv(path)
        st.write('数据预览')
        st.dataframe(df, width='stretch')
        algorithms = list_algorithms('error_detection')
        if not algorithms:
            st.warning('当前模块尚未注册算法。')
            return
        labels = {spec.algorithm_id: spec.label for spec in algorithms}
        algorithm_id = st.selectbox(
            '选择算法',
            options=[spec.algorithm_id for spec in algorithms],
            format_func=labels.get,
        )
        if st.button('运行所选算法'):
            with st.spinner('算法运行中...'):
                result = execute_algorithm(
                    module_id='error_detection',
                    algorithm_id=algorithm_id,
                    inputs={'dataset_path': path},
                    params={},
                )
            st.success(f'检测完成：{len(result.predictions)} 个疑似缺失单元格')
            st.dataframe(result.predictions, width='stretch')
            saved = save_experiment(
                result,
                dataset_id='uploaded_csv' if uploaded else 'errors_demo_v1',
                config={'algorithm_id': algorithm_id},
            )
            st.caption(f'实验记录已保存：{saved.name}')
    except AlgorithmRuntimeError as exc:
        st.error(f'算法运行失败：{exc}')
    except Exception as exc:
        st.error(f'数据加载或运行失败：{exc}')
