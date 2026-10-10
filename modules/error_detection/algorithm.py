from core.base import AlgorithmResult


def detect_missing(df):
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
