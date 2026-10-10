from pathlib import Path
import json

import pytest

from core.base import AlgorithmResult
from core.datasets import load_csv
from core.experiment import save_experiment
from modules.error_detection import detect_missing

SAMPLE = Path(__file__).resolve().parents[1] / 'datasets/samples/errors_demo.csv'


def test_csv_and_baseline():
    df = load_csv(SAMPLE)
    assert len(df) == 4
    assert '__row_id' in df.columns
    result = detect_missing(df)
    assert result.task_type == 'error_detection'
    assert len(result.predictions) == 2
    assert {(x['row_id'], x['column']) for x in result.predictions} == {('1', 'city'), ('2', 'age')}


def test_experiment_record(tmp_path):
    result = detect_missing(load_csv(SAMPLE))
    path = save_experiment(
        result,
        'errors_demo_v1',
        config={'seed': 0, 'method': 'missing_value_baseline'},
        output_dir=tmp_path,
    )
    record = json.loads(path.read_text(encoding='utf-8'))
    assert set(record) == {
        'experiment_id',
        'created_at',
        'task_type',
        'algorithm',
        'dataset_id',
        'config',
        'metrics',
        'metadata',
        'predictions',
    }
    assert record['dataset_id'] == 'errors_demo_v1'
    assert record['config'] == {'seed': 0, 'method': 'missing_value_baseline'}
    assert record['task_type'] == result.task_type
    assert record['algorithm'] == result.algorithm
    assert record['metrics'] == result.metrics
    assert record['metadata'] == result.metadata
    assert len(record['predictions']) == 2


def test_reserved_column(tmp_path):
    path = tmp_path / 'bad.csv'
    path.write_text('__row_id,name\n1,a\n', encoding='utf-8')
    with pytest.raises(ValueError):
        load_csv(path)


def test_algorithm_result_required_fields():
    with pytest.raises(TypeError):
        AlgorithmResult(task_type='error_detection', algorithm='baseline')
    with pytest.raises(ValueError, match='task_type'):
        AlgorithmResult('', 'baseline', []).validate()
    with pytest.raises(ValueError, match='algorithm'):
        AlgorithmResult('error_detection', '', []).validate()
    with pytest.raises(ValueError, match='predictions'):
        AlgorithmResult('error_detection', 'baseline', None).validate()


@pytest.mark.parametrize(
    ('field_name', 'kwargs'),
    [
        ('metrics', {'metrics': []}),
        ('metadata', {'metadata': []}),
    ],
)
def test_algorithm_result_dictionary_fields(field_name, kwargs):
    with pytest.raises(TypeError, match=field_name):
        AlgorithmResult('error_detection', 'baseline', [], **kwargs).validate()


def test_algorithm_result_json_serialization_contract():
    result = AlgorithmResult(
        task_type='error_detection',
        algorithm='baseline',
        predictions=[{'row_id': '0', 'column': 'age', 'score': 1.0}],
        metrics={'precision': 1.0},
        metadata={'seed': 0},
    )
    payload = result.to_dict()
    assert json.loads(json.dumps(payload, ensure_ascii=False)) == payload

    with pytest.raises(TypeError, match='JSON serializable'):
        AlgorithmResult('error_detection', 'baseline', [{'bad': {1, 2}}]).validate()


def test_experiment_rejects_invalid_config(tmp_path):
    result = AlgorithmResult('error_detection', 'baseline', [])
    with pytest.raises(TypeError, match='config'):
        save_experiment(result, 'dataset', config=[], output_dir=tmp_path)
    with pytest.raises(ValueError, match='dataset_id'):
        save_experiment(result, '', output_dir=tmp_path)
