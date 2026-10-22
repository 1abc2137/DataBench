"""生成 quality_impact 模块使用的公开数据集 CSV。

一次性准备脚本：把两个公开二分类数据集转成统一格式，落到
``datasets/samples/`` 下，供页面直接加载、实验可复现。

- breast_cancer.csv：Breast Cancer Wisconsin (Diagnostic)，来自 scikit-learn
  内置 ``load_breast_cancer()``（569 行，30 个数值特征，标签 0=恶性 / 1=良性）。
  完全离线、结果确定，不依赖网络。

- adult.csv：UCI Adult（Census Income，人口普查收入预测），
  https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data
  （训练集 32561 行，14 个特征，标签 0=<=50K / 1=>50K）。
  预处理：跳过缺失值 ``?`` 所在行、去首尾空白、``income`` 映射为 0/1。

统一约定（与模块其余数据一致）：目标列名为 ``label``，二分类 0/1。

脚本幂等：目标 CSV 已存在时跳过，重复运行不会重下网络数据。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.datasets import load_breast_cancer

SAMPLES = Path(__file__).resolve().parents[2] / 'datasets' / 'samples'

ADULT_URL = 'https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data'
ADULT_COLS = [
    'age', 'workclass', 'fnlwgt', 'education', 'education-num',
    'marital-status', 'occupation', 'relationship', 'race', 'sex',
    'capital-gain', 'capital-loss', 'hours-per-week', 'native-country', 'income',
]


def _write(df: pd.DataFrame, name: str) -> None:
    path = SAMPLES / name
    if path.exists():
        print(f'跳过（已存在）：{path.name}（{len(df)} 行）')
        return
    df.to_csv(path, index=False)
    print(f'已生成：{path.name}（{len(df)} 行 × {len(df.columns)} 列）')


def prepare_breast_cancer() -> None:
    data = load_breast_cancer()
    df = pd.DataFrame(data.data, columns=data.feature_names)
    df['label'] = data.target
    _write(df, 'breast_cancer.csv')


def prepare_adult() -> None:
    adult = pd.read_csv(
        ADULT_URL, header=None, names=ADULT_COLS,
        skipinitialspace=True, na_values='?',
    )
    for col in adult.select_dtypes(include='object').columns:
        adult[col] = adult[col].str.strip()
    adult = adult.dropna().reset_index(drop=True)
    adult['label'] = (adult['income'] == '>50K').astype(int)
    adult = adult.drop(columns=['income'])
    _write(adult, 'adult.csv')


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    prepare_breast_cancer()
    prepare_adult()


if __name__ == '__main__':
    main()
