import json
from pathlib import Path

import pytest

from core.algorithm_registry import get_algorithm
from core.datasets import load_csv
from core.executor import execute_algorithm
from core.registry import get_module
from modules.error_detection.acceptance import run_acceptance
from modules.error_detection.page import render


SAMPLE = Path(__file__).resolve().parents[2] / 'datasets' / 'samples' / 'errors_demo.csv'


def test_error_detection_page_entrypoint():
    spec = get_module('error_detection')
    assert spec.page_entrypoint == 'modules.error_detection.page:render'
    assert callable(render)


def test_normal_sample_returns_contract_result(tmp_path):
    result = execute_algorithm(
        'error_detection',
        'missing_value_baseline',
        {'dataset_path': SAMPLE},
        workspace_root=tmp_path,
    )
    assert result.validate().task_type == 'error_detection'
    assert len(result.predictions) == 2


def test_algorithm_is_registered():
    spec = get_algorithm('error_detection', 'missing_value_baseline')
    assert spec.runtime == 'builtin'
    assert spec.label == '缺失值检测 Baseline'


def test_invalid_reserved_row_id_is_rejected(tmp_path):
    invalid = tmp_path / 'invalid.csv'
    invalid.write_text('__row_id,name\n0,Alice\n', encoding='utf-8')
    with pytest.raises(ValueError, match='Reserved column'):
        load_csv(invalid)


def test_acceptance_smoke_saves_complete_experiment(tmp_path):
    evidence = run_acceptance(tmp_path)
    assert evidence.module_id == 'error_detection'
    record = json.loads(evidence.experiment_files[0].read_text(encoding='utf-8'))
    assert record['task_type'] == 'error_detection'
    assert record['algorithm'] == 'missing_value_baseline'
    assert len(record['predictions']) == 2
