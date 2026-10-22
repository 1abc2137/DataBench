from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.base import AlgorithmResult
from core.datasets import load_csv
from core.registry import get_module
from modules.quality_impact.algorithms.duplicate_impact.algorithm import run as run_duplicate
from modules.quality_impact.algorithms.missing_baseline.algorithm import run as run_missing
from modules.quality_impact.algorithms.outlier_impact.algorithm import run as run_outlier
from modules.quality_impact.common import (
    aggregate_duplicates,
    drop_duplicate_rows,
    drop_missing_rows,
    drop_outlier_rows,
    impute_median_mode,
    inject_duplicate,
    inject_missing,
    inject_outlier,
    numeric_columns,
    run_quality_experiment,
    winsorize_outliers,
)
from modules.quality_impact.page import render

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / 'datasets/samples/quality_demo.csv'
BREAST_CANCER = ROOT / 'datasets/samples/breast_cancer.csv'
ADULT = ROOT / 'datasets/samples/adult.csv'


def _demo_df() -> pd.DataFrame:
    return load_csv(DEMO)


def _feats(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in ('label', '__row_id')]


def test_quality_impact_page_entrypoint():
    spec = get_module('quality_impact')
    assert spec.page_entrypoint == 'modules.quality_impact.page:render'
    assert callable(render)


# ---------------------------------------------------------------------------
# 三个算法包：返回四种条件
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('run_fn,algo_id', [
    (run_missing, 'missing_baseline'),
    (run_outlier, 'outlier_impact'),
    (run_duplicate, 'duplicate_impact'),
])
def test_algorithm_run_returns_four_conditions(run_fn, algo_id):
    result = run_fn(
        {'dataset_path': str(DEMO)},
        {'target': 'label', 'rate': 0.1, 'seed': 0, 'classifier': 'logreg'},
    )
    assert isinstance(result, AlgorithmResult)
    assert result.algorithm == algo_id
    conditions = [c['condition'] for c in result.predictions['comparisons']]
    assert conditions == ['clean', 'polluted', 'strategy1', 'strategy2']
    assert 'clean_f1' in result.metrics
    result.to_dict()  # 结果必须 JSON 可序列化（不含模型对象）


# ---------------------------------------------------------------------------
# 扰动器
# ---------------------------------------------------------------------------

def test_inject_missing_rate_approximate():
    polluted = inject_missing(_demo_df(), 'label', 0.5, seed=0)
    rate = polluted[_feats(polluted)].isna().sum().sum() / (len(polluted) * len(_feats(polluted)))
    assert 0.4 <= rate <= 0.6


def test_inject_missing_rate_zero_unchanged():
    polluted = inject_missing(_demo_df(), 'label', 0.0, seed=0)
    assert polluted[_feats(polluted)].isna().sum().sum() == 0


def test_inject_duplicate_row_count():
    df = _demo_df()
    polluted = inject_duplicate(df, 'label', 0.3, seed=0)
    assert len(polluted) == len(df) + round(len(df) * 0.3)


def test_inject_outlier_preserves_shape_and_changes():
    df = _demo_df()
    polluted = inject_outlier(df, 'label', 0.3, seed=0)
    assert len(polluted) == len(df)
    assert not polluted.equals(df)


# ---------------------------------------------------------------------------
# 清洗器
# ---------------------------------------------------------------------------

def test_drop_missing_rows_removes_nan():
    polluted = inject_missing(_demo_df(), 'label', 0.3, seed=0)
    cleaned = drop_missing_rows(polluted, 'label')
    assert cleaned[_feats(cleaned)].isna().sum().sum() == 0
    assert len(cleaned) < len(polluted)


def test_impute_median_mode_no_nan():
    polluted = inject_missing(_demo_df(), 'label', 0.3, seed=0)
    cleaned = impute_median_mode(polluted, 'label')
    assert cleaned[_feats(cleaned)].isna().sum().sum() == 0
    assert len(cleaned) == len(polluted)


def test_drop_duplicate_rows_removes_dupes():
    polluted = inject_duplicate(_demo_df(), 'label', 0.3, seed=0)
    cleaned = drop_duplicate_rows(polluted, 'label')
    assert cleaned.duplicated(subset=_feats(cleaned)).sum() == 0


def test_aggregate_duplicates_removes_dupes():
    polluted = inject_duplicate(_demo_df(), 'label', 0.3, seed=0)
    cleaned = aggregate_duplicates(polluted, 'label')
    assert cleaned.duplicated(subset=_feats(cleaned)).sum() == 0


def test_winsorize_reduces_range():
    df = _demo_df()
    polluted = inject_outlier(df, 'label', 0.3, seed=0)
    cleaned = winsorize_outliers(polluted, 'label')
    for col in numeric_columns(df, 'label'):
        poll = pd.to_numeric(polluted[col], errors='coerce').astype(float)
        clean = pd.to_numeric(cleaned[col], errors='coerce').astype(float)
        assert clean.max() <= poll.max() + 1e-9
        assert clean.min() >= poll.min() - 1e-9


# ---------------------------------------------------------------------------
# 公开数据集：Breast Cancer / Adult 可加载、可跑通
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('path,min_rows', [
    (BREAST_CANCER, 500),
    (ADULT, 20000),
])
def test_public_datasets_load(path, min_rows):
    df = load_csv(path)
    assert 'label' in df.columns
    assert len(df) >= min_rows
    assert set(pd.to_numeric(df['label'], errors='coerce').dropna().unique()) == {0.0, 1.0}


@pytest.mark.parametrize('path', [BREAST_CANCER, ADULT])
def test_public_datasets_run_experiment(path):
    result = run_quality_experiment(load_csv(path), 'label', 'missing', 0.1, 0, 'logreg')
    conditions = [c['condition'] for c in result['comparisons']]
    assert conditions == ['clean', 'polluted', 'strategy1', 'strategy2']
    for f1 in result['downstream_metrics'].values():
        assert f1 is None or 0.0 <= f1 <= 1.0


# ---------------------------------------------------------------------------
# 任务书要求的健壮性：目标列缺失 / 单一类别 / 无法划分 / 不可序列化
# ---------------------------------------------------------------------------

def test_missing_target_raises():
    with pytest.raises(ValueError):
        run_quality_experiment(_demo_df(), 'nonexistent', 'missing', 0.1, 0, 'logreg')


def test_single_class_raises():
    df = _demo_df()
    df['label'] = '0'
    with pytest.raises(Exception):
        run_quality_experiment(df, 'label', 'missing', 0.1, 0, 'logreg')


def test_too_few_samples_raises():
    df = _demo_df().head(3)
    with pytest.raises(Exception):
        run_quality_experiment(df, 'label', 'missing', 0.1, 0, 'logreg')


def test_algorithm_result_rejects_unserializable():
    from sklearn.linear_model import LogisticRegression
    result = AlgorithmResult(
        task_type='quality_impact',
        algorithm='x',
        predictions={'model': LogisticRegression()},
        metrics={},
        metadata={},
    )
    with pytest.raises(TypeError):
        result.validate()
