from pathlib import Path

import pandas as pd
import streamlit as st

from core.algorithm_registry import list_algorithms
from core.datasets import load_csv
from core.executor import execute_algorithm
from core.experiment import save_experiment
from core.runtime_errors import AlgorithmRuntimeError


ROOT = Path(__file__).resolve().parents[2]
BUILTIN_DATASETS = {
    'quality_demo': {
        'label': '质量演示数据（合成）',
        'path': ROOT / 'datasets/samples/quality_demo.csv',
        'dataset_id': 'quality_demo_v1',
    },
    'breast_cancer': {
        'label': 'Breast Cancer Wisconsin（UCI）',
        'path': ROOT / 'datasets/samples/breast_cancer.csv',
        'dataset_id': 'breast_cancer_v1',
    },
    'adult': {
        'label': 'Adult 人口收入（UCI）',
        'path': ROOT / 'datasets/samples/adult.csv',
        'dataset_id': 'adult_v1',
    },
}

CONDITION_ORDER = ['clean', 'polluted', 'strategy1', 'strategy2']
CONDITION_LABELS = {
    'clean': '原始干净',
    'polluted': '污染后',
    'strategy1': '策略一（简单清洗）',
    'strategy2': '策略二（统计清洗）',
}

CLASSIFIER_LABELS = {'logreg': 'Logistic Regression', 'random_forest': 'Random Forest'}

METRIC_LABELS = {'accuracy': '准确率', 'precision': '精确率', 'recall': '召回率', 'f1': 'F1'}

QUALITY_LABELS = {
    'error_rate': '扰动比例',
    'rows_clean': '原始行数',
    'rows_polluted': '污染后行数',
    'rows_strategy1': '策略一行数',
    'rows_strategy2': '策略二行数',
    'missing_rate': '缺失率',
    'duplicate_rate': '重复率',
}


def _run(algorithm_id: str, source, classifier: str, rate: float, seed: int):
    return execute_algorithm(
        module_id='quality_impact',
        algorithm_id=algorithm_id,
        inputs={'dataset_path': source},
        params={'target': 'label', 'rate': rate, 'seed': seed, 'classifier': classifier},
    )


def _f1_by_condition(result) -> dict[str, float | None]:
    return {c['condition']: c['f1'] for c in result.predictions.get('comparisons', [])}


def _format_quality_value(key: str, value) -> str:
    if value is None:
        return '—'
    if 'rate' in key:
        return f'{value:.2%}'
    if isinstance(value, (int, float)):
        return f'{value:,}'
    return str(value)


def _render_single(result, conditions) -> None:
    f1 = _f1_by_condition(result)
    clean_f1 = f1.get('clean')

    cols = st.columns(len(conditions))
    for col, cond in zip(cols, conditions):
        value = f1.get(cond)
        delta = None
        if cond != 'clean' and value is not None and clean_f1 is not None:
            delta = value - clean_f1
        col.metric(
            CONDITION_LABELS[cond],
            f'{value:.3f}' if value is not None else '—',
            delta=f'{delta:+.3f}' if delta is not None else None,
            delta_color='off',
        )
    st.caption('Δ 表示相对「原始干净」的 F1 变化（正 = 上升，负 = 下降）')

    comparisons = result.predictions.get('comparisons', [])
    comp_df = pd.DataFrame(comparisons).set_index('condition')
    comp_df = comp_df.loc[[c for c in conditions if c in comp_df.index]]
    comp_df = comp_df[['accuracy', 'precision', 'recall', 'f1']]
    comp_df.index = [CONDITION_LABELS[c] for c in comp_df.index]
    comp_df = comp_df.rename(columns=METRIC_LABELS)
    styler = comp_df.style.format('{:.2%}').highlight_max(subset=['F1'], color='#d5f5e3')
    st.markdown('#### 条件对比（下游指标）')
    st.dataframe(styler, width='stretch')

    with st.expander('数据质量指标（行数与污染率）'):
        quality = result.predictions.get('quality_metrics', {})
        q_df = pd.DataFrame(
            [{'指标': QUALITY_LABELS.get(k, k), '值': _format_quality_value(k, v)} for k, v in quality.items()]
        )
        st.dataframe(q_df, width='stretch', hide_index=True)


def render() -> None:
    # ---- 数据 ----
    st.markdown('#### 数据')
    uploaded = st.file_uploader('上传 CSV（不超过 10MB，上传后优先）', type=['csv'])
    if uploaded is not None:
        source = uploaded
        dataset_id = 'uploaded_csv'
    else:
        dataset_key = st.selectbox(
            '选择内置数据集',
            list(BUILTIN_DATASETS),
            format_func=lambda k: BUILTIN_DATASETS[k]['label'],
        )
        source = BUILTIN_DATASETS[dataset_key]['path']
        dataset_id = BUILTIN_DATASETS[dataset_key]['dataset_id']

    algorithms = list_algorithms('quality_impact')
    if not algorithms:
        st.warning('当前模块尚未注册算法。')
        return

    try:
        df = load_csv(source)
    except Exception as exc:
        st.error(f'数据加载失败：{exc}')
        return

    n_features = len(df.columns) - 2  # 去掉 __row_id 与 label
    counts = df['label'].value_counts()
    dist = '｜'.join(f'{k} → {v}（{v / len(df):.1%}）' for k, v in counts.items())
    st.caption(f'共 {len(df)} 行 × {n_features} 个特征；label 分布：{dist}')
    st.dataframe(df.drop(columns=['__row_id']).head(20), width='stretch')

    # ---- 实验设置 ----
    st.markdown('#### 实验设置')
    labels = {spec.algorithm_id: spec.label for spec in algorithms}
    col1, col2 = st.columns(2)
    algorithm_id = col1.selectbox(
        '错误类型（算法）',
        options=[spec.algorithm_id for spec in algorithms],
        format_func=labels.get,
    )
    classifier = col2.selectbox('分类器', list(CLASSIFIER_LABELS), format_func=CLASSIFIER_LABELS.get)
    col3, col4 = st.columns(2)
    rate = col3.slider('扰动比例', 0.0, 0.5, 0.1, 0.05)
    seed = col4.number_input('随机种子', 0, 1000, 0, 1)
    conditions = st.multiselect(
        '对比条件',
        options=list(CONDITION_LABELS),
        default=list(CONDITION_LABELS),
        format_func=CONDITION_LABELS.get,
    )

    col_run1, col_run2 = st.columns(2)
    run_single = col_run1.button('运行单点实验', type='primary', width='stretch')
    run_curve = col_run2.button('绘制扰动比例 → F1 曲线', width='stretch')

    if run_single:
        with st.spinner('算法运行中...'):
            try:
                result = _run(algorithm_id, source, classifier, rate, seed)
            except AlgorithmRuntimeError as exc:
                st.error(f'算法运行失败：{exc}')
                return
            except Exception as exc:
                st.error(f'运行出错：{exc}')
                return

        st.success('运行完成')
        _render_single(result, conditions)
        saved = save_experiment(
            result,
            dataset_id=dataset_id,
            config={'algorithm_id': algorithm_id, 'rate': rate, 'seed': seed, 'classifier': classifier},
        )
        st.caption(f'实验记录已保存：{saved.name}')

    if run_curve:
        if not conditions:
            st.warning('请至少选择一个「对比条件」。')
            return
        rates = [round(i * 0.05, 2) for i in range(0, 11)]
        rows = {}
        with st.spinner('扫描扰动比例中（0 ~ 0.5，共 11 次）...'):
            for r in rates:
                try:
                    res = _run(algorithm_id, source, classifier, r, seed)
                except (AlgorithmRuntimeError, Exception) as exc:
                    st.error(f'扰动比例 {r} 运行失败：{exc}')
                    return
                rows[r] = {c['condition']: c['f1'] for c in res.predictions.get('comparisons', [])}

        curve_df = pd.DataFrame.from_dict(rows, orient='index')
        curve_df = curve_df.rename(columns=CONDITION_LABELS)
        curve_df.index.name = '扰动比例'
        show_cols = [CONDITION_LABELS[c] for c in conditions if c in CONDITION_LABELS]
        st.markdown('#### 扰动比例 → F1 变化')
        st.line_chart(curve_df[show_cols], width='stretch')
