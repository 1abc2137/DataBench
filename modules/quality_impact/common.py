"""quality_impact 组共享框架：扰动器 + 清洗器 + 统一实验编排。

借鉴 CleanML 的「错误类型 × 清洗策略」矩阵，把缺失 / 离群 / 重复三种
错误类型的扰动、清洗和下游评估收敛到同一套接口，供各算法包薄封装复用。

关键约束（任务书「不做事项」）：
- 只污染 / 清洗训练集，测试集全程干净；
- 插补 / 截断的统计量（中位数 / 众数 / 分位数）只用训练集拟合。
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from core.base import AlgorithmResult
from core.datasets import load_csv

CLASSIFIERS = {
    'logreg': lambda: make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=1000, random_state=0, class_weight='balanced')
    ),
    'random_forest': lambda: RandomForestClassifier(
        n_estimators=50, random_state=0, n_jobs=-1, class_weight='balanced'
    ),
}


def _feature_cols(df: pd.DataFrame, target: str) -> list[str]:
    return [c for c in df.columns if c not in (target, '__row_id')]


def numeric_columns(df: pd.DataFrame, target: str) -> list[str]:
    """识别数值特征列（能被解析成数值的列）。"""
    return [c for c in _feature_cols(df, target) if pd.to_numeric(df[c], errors='coerce').notna().any()]


def split_dataframe(df: pd.DataFrame, target: str, seed: int = 0, test_size: float = 0.25):
    """按固定种子划分原始 DataFrame（先划分再扰动，保证测试集干净）。"""
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=seed, stratify=df[target])
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def to_matrix(df: pd.DataFrame, target: str) -> tuple[pd.DataFrame, np.ndarray]:
    """把 DataFrame 编码成数值特征矩阵与 int 目标数组（类别列做整数编码）。"""
    X = df.drop(columns=[target], errors='ignore')
    X = X.drop(columns=['__row_id'], errors='ignore')
    encoded = pd.DataFrame(index=X.index)
    for col in X.columns:
        numeric = pd.to_numeric(X[col], errors='coerce')
        encoded[col] = numeric if numeric.notna().any() else pd.factorize(X[col])[0]
    y = pd.to_numeric(df[target], errors='coerce').astype(int).to_numpy()
    return encoded, y


def evaluate(model, X_test, y_test) -> dict[str, float]:
    pred = model.predict(X_test)
    return {
        'accuracy': float(accuracy_score(y_test, pred)),
        'precision': float(precision_score(y_test, pred, zero_division=0)),
        'recall': float(recall_score(y_test, pred, zero_division=0)),
        'f1': float(f1_score(y_test, pred, zero_division=0)),
    }


def train_eval(X_train, y_train, X_test, y_test, classifier: str = 'logreg') -> dict[str, float]:
    model = CLASSIFIERS[classifier]()
    model.fit(X_train, y_train)
    return evaluate(model, X_test, y_test)


# ---------------------------------------------------------------------------
# 扰动器：签名 perturb(train_df, target, rate, seed) -> polluted_df
# ---------------------------------------------------------------------------

def inject_missing(df: pd.DataFrame, target: str, rate: float, seed: int) -> pd.DataFrame:
    """对每列特征按 rate 注入缺失值（NaN）。"""
    rng = np.random.default_rng(seed)
    polluted = df.copy()
    for col in _feature_cols(df, target):
        mask = rng.random(len(polluted)) < rate
        polluted.loc[mask, col] = np.nan
    return polluted


def inject_outlier(df: pd.DataFrame, target: str, rate: float, seed: int) -> pd.DataFrame:
    """对数值特征列按 rate 注入极端离群值（该列 mean ± 5*std）。"""
    rng = np.random.default_rng(seed)
    polluted = df.copy()
    for col in numeric_columns(df, target):
        vals = pd.to_numeric(polluted[col], errors='coerce').astype(float).to_numpy()
        mean, std = vals.mean(), vals.std()
        if pd.isna(std) or std == 0:
            continue
        mask = rng.random(len(vals)) < rate
        if not mask.any():
            continue
        offset = rng.choice([-1.0, 1.0], size=int(mask.sum())) * 5.0 * std
        vals[mask] = mean + offset
        polluted[col] = vals
    return polluted


def inject_duplicate(df: pd.DataFrame, target: str, rate: float, seed: int) -> pd.DataFrame:
    """随机复制 rate 比例的行（连同标签）追加到末尾。"""
    rng = np.random.default_rng(seed)
    n_dup = int(round(len(df) * rate))
    if n_dup <= 0:
        return df.copy()
    idx = rng.integers(0, len(df), size=n_dup)
    return pd.concat([df, df.iloc[idx]], ignore_index=True)


PERTURBERS = {
    'missing': inject_missing,
    'outlier': inject_outlier,
    'duplicate': inject_duplicate,
}

# ---------------------------------------------------------------------------
# 清洗器：签名 clean(polluted_df, target) -> cleaned_df（只用训练集统计量）
# ---------------------------------------------------------------------------

def drop_missing_rows(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """简单策略：删除含缺失值的行。"""
    return df.dropna(subset=_feature_cols(df, target))


def impute_median_mode(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """统计策略：数值列中位数填充，类别列众数填充。"""
    cleaned = df.copy()
    for col in _feature_cols(df, target):
        numeric = pd.to_numeric(cleaned[col], errors='coerce')
        if numeric.notna().any():
            cleaned[col] = numeric.fillna(numeric.median())
        else:
            mode = cleaned[col].mode()
            cleaned[col] = cleaned[col].fillna(mode.iloc[0] if not mode.empty else 'missing')
    return cleaned


def drop_outlier_rows(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """简单策略：删除数值列落在 [Q1-1.5IQR, Q3+1.5IQR] 之外的行。"""
    keep = pd.Series(True, index=df.index)
    for col in numeric_columns(df, target):
        vals = pd.to_numeric(df[col], errors='coerce').astype(float)
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        keep &= (vals >= lo) & (vals <= hi)
    return df[keep]


def winsorize_outliers(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """统计策略：把数值列截断到 [Q1-1.5IQR, Q3+1.5IQR] 边界（保留行数）。"""
    cleaned = df.copy()
    for col in numeric_columns(df, target):
        vals = pd.to_numeric(cleaned[col], errors='coerce').astype(float)
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        cleaned[col] = vals.clip(lo, hi)
    return cleaned


def drop_duplicate_rows(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """简单策略：删除完全重复的特征行（保留首条）。"""
    return df.drop_duplicates(subset=_feature_cols(df, target), keep='first')


def aggregate_duplicates(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """统计策略：把重复行聚合为一条（数值列取均值，类别列取首条）。"""
    feats = _feature_cols(df, target)
    num_cols = numeric_columns(df, target)
    cat_cols = [c for c in feats if c not in num_cols]
    pieces: list[pd.DataFrame] = []
    for _, group in df.groupby(feats, dropna=False, sort=False):
        if len(group) == 1:
            pieces.append(group)
            continue
        row: dict = {}
        for col in num_cols:
            row[col] = pd.to_numeric(group[col], errors='coerce').mean()
        for col in cat_cols:
            row[col] = group[col].iloc[0]
        row[target] = group[target].iloc[0]
        pieces.append(pd.DataFrame([row]))
    if not pieces:
        return df.iloc[0:0]
    result = pd.concat(pieces, ignore_index=True)
    return result.reindex(columns=feats + [target])


CLEANERS = {
    'missing': [
        ('drop_rows', '删除缺失行', drop_missing_rows),
        ('impute', '中位数/众数插补', impute_median_mode),
    ],
    'outlier': [
        ('drop_outliers', '删除离群行', drop_outlier_rows),
        ('winsorize', '离群值截断', winsorize_outliers),
    ],
    'duplicate': [
        ('drop_duplicates', '删除重复记录', drop_duplicate_rows),
        ('aggregate', '重复记录聚合', aggregate_duplicates),
    ],
}

_EMPTY_METRICS = {'accuracy': None, 'precision': None, 'recall': None, 'f1': None}


def _train_cleaned(cleaned_df, target, X_test, y_test, classifier) -> dict[str, float | None]:
    if cleaned_df is None or len(cleaned_df) < 5:
        return dict(_EMPTY_METRICS)
    X, y = to_matrix(cleaned_df, target)
    if len(np.unique(y)) < 2:
        return dict(_EMPTY_METRICS)
    return train_eval(X, y, X_test, y_test, classifier)


def _quality_metrics(train_df, polluted_df, cleaned1_df, cleaned2_df, target, error_type, rate) -> dict:
    feats = _feature_cols(polluted_df, target)
    metrics = {
        'error_rate': float(rate),
        'rows_clean': int(len(train_df)),
        'rows_polluted': int(len(polluted_df)),
        'rows_strategy1': int(len(cleaned1_df)),
        'rows_strategy2': int(len(cleaned2_df)),
    }
    if error_type == 'missing':
        metrics['missing_rate'] = float(polluted_df[feats].isna().sum().sum() / (len(polluted_df) * len(feats)))
    elif error_type == 'duplicate':
        metrics['duplicate_rate'] = float(polluted_df.duplicated(subset=feats).sum() / len(polluted_df))
    return metrics


def run_quality_experiment(df, target, error_type, rate, seed, classifier) -> dict:
    """跑完整四种条件对比：clean / polluted / strategy1 / strategy2。"""
    if error_type not in PERTURBERS:
        raise ValueError(f'未知错误类型: {error_type}')
    if target not in df.columns:
        raise ValueError(f'目标列 {target!r} 不存在于数据中')

    train_df, test_df = split_dataframe(df, target, seed=seed)
    X_train, y_train = to_matrix(train_df, target)
    X_test, y_test = to_matrix(test_df, target)

    clean_metrics = train_eval(X_train, y_train, X_test, y_test, classifier)

    polluted_df = PERTURBERS[error_type](train_df, target, rate, seed)
    X_polluted, y_polluted = to_matrix(polluted_df, target)
    # polluted 条件不做规范清洗；缺失值用 0 填充仅为让模型可运行（语义见 metadata note）
    polluted_metrics = train_eval(X_polluted.fillna(0.0), y_polluted, X_test, y_test, classifier)

    (_, s1_label, s1_fn), (_, s2_label, s2_fn) = CLEANERS[error_type]
    cleaned1_df = s1_fn(polluted_df, target)
    cleaned2_df = s2_fn(polluted_df, target)
    strategy1_metrics = _train_cleaned(cleaned1_df, target, X_test, y_test, classifier)
    strategy2_metrics = _train_cleaned(cleaned2_df, target, X_test, y_test, classifier)

    comparisons = [
        {'condition': 'clean', **clean_metrics},
        {'condition': 'polluted', **polluted_metrics},
        {'condition': 'strategy1', **strategy1_metrics},
        {'condition': 'strategy2', **strategy2_metrics},
    ]
    downstream_metrics = {
        'clean_f1': clean_metrics['f1'],
        'polluted_f1': polluted_metrics['f1'],
        'strategy1_f1': strategy1_metrics['f1'],
        'strategy2_f1': strategy2_metrics['f1'],
    }

    return {
        'quality_metrics': _quality_metrics(train_df, polluted_df, cleaned1_df, cleaned2_df, target, error_type, rate),
        'downstream_metrics': downstream_metrics,
        'comparisons': comparisons,
        'metadata': {
            'target': target,
            'error_type': error_type,
            'rate': rate,
            'seed': seed,
            'classifier': classifier,
            'strategy1': s1_label,
            'strategy2': s2_label,
            'note': 'polluted 条件对缺失值用 0 填充仅为让模型可运行，不视为规范清洗',
        },
    }


def build_algorithm_run(error_type: str, algorithm_id: str):
    """工厂：生成符合 AlgorithmResult 合约的 run(inputs, params)。"""
    def run(inputs: dict, params: dict) -> AlgorithmResult:
        dataset_path = inputs.get('dataset_path')
        if not isinstance(dataset_path, str) or not dataset_path.strip():
            raise ValueError('inputs.dataset_path must be a non-empty path')
        target = params.get('target', 'label')
        rate = float(params.get('rate', 0.1))
        seed = int(params.get('seed', 0))
        classifier = params.get('classifier', 'logreg')

        df = load_csv(dataset_path)
        payload = run_quality_experiment(df, target, error_type, rate, seed, classifier)

        return AlgorithmResult(
            task_type='quality_impact',
            algorithm=algorithm_id,
            predictions={
                'quality_metrics': payload['quality_metrics'],
                'downstream_metrics': payload['downstream_metrics'],
                'comparisons': payload['comparisons'],
            },
            metrics=payload['downstream_metrics'],
            metadata=payload['metadata'],
        ).validate()

    return run
