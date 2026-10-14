from typing import Any

from core.base import AlgorithmResult
from core.datasets import load_csv


def run(inputs: dict[str, Any], params: dict[str, Any]) -> AlgorithmResult:
    dataset_path = inputs.get('dataset_path')
    if not isinstance(dataset_path, str) or not dataset_path.strip():
        raise ValueError('inputs.dataset_path must be a non-empty path')

    df = load_csv(dataset_path)
    predictions = []
    for _, row in df.iterrows():
        for col in df.columns:
            if col == '__row_id':
                continue
            if str(row[col]).strip() == '':
                predictions.append({
                    'row_id': str(row['__row_id']),
                    'column': str(col),
                    'error_type': 'missing',
                    'score': 1.0,
                })
    return AlgorithmResult(
        task_type='error_detection',
        algorithm='missing_value_baseline',
        predictions=predictions,
        metadata={'count': len(predictions)},
    ).validate()
