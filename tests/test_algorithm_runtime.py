import io
import json

import pytest

import core.executor as executor_module
from core.algorithm_registry import AlgorithmSpec, get_algorithm, list_algorithms
from core.executor import execute_algorithm
from core.runtime_errors import AlgorithmEnvironmentError, AlgorithmProtocolError


class UploadedCsv(io.BytesIO):
    name = 'uploaded.csv'


def test_registry_discovers_error_detection_baseline():
    algorithms = list_algorithms('error_detection')
    assert [spec.algorithm_id for spec in algorithms] == ['missing_value_baseline']
    assert algorithms[0].runtime == 'builtin'
    assert get_algorithm('error_detection', 'missing_value_baseline') == algorithms[0]


def test_registry_rejects_unknown_algorithm():
    with pytest.raises(KeyError, match='Unknown algorithm'):
        get_algorithm('error_detection', 'not_registered')


def test_executor_materializes_upload_and_writes_runtime_evidence(tmp_path):
    upload = UploadedCsv(b'name,city\nAlice,Shanghai\nBob,\n')
    result = execute_algorithm(
        'error_detection',
        'missing_value_baseline',
        {'dataset_path': upload},
        workspace_root=tmp_path,
    )

    run_dir = tmp_path / result.metadata['run_id']
    assert result.metadata['runtime'] == 'builtin'
    assert len(result.predictions) == 1
    assert (run_dir / 'input' / 'uploaded.csv').is_file()
    assert (run_dir / 'request.json').is_file()
    assert (run_dir / 'stdout.log').is_file()
    assert (run_dir / 'stderr.log').is_file()
    payload = json.loads((run_dir / 'result.json').read_text(encoding='utf-8'))
    assert payload['algorithm'] == 'missing_value_baseline'
    assert payload['metadata']['run_id'] == result.metadata['run_id']


def test_executor_rejects_invalid_params(tmp_path):
    with pytest.raises(TypeError, match='params'):
        execute_algorithm(
            'error_detection',
            'missing_value_baseline',
            {'dataset_path': 'unused.csv'},
            params=[],
            workspace_root=tmp_path,
        )


def test_uv_runtime_builds_frozen_project_command(tmp_path, monkeypatch):
    spec = AlgorithmSpec(
        module_id='error_detection',
        algorithm_id='isolated_demo',
        label='Isolated Demo',
        runtime='uv',
        entrypoint='runner.py',
        manifest_path=tmp_path / 'algorithm.json',
        project_dir=tmp_path,
    )
    monkeypatch.setattr(executor_module.shutil, 'which', lambda name: 'uv.exe')
    command, working_dir = executor_module._runtime_command(
        spec,
        tmp_path / 'request.json',
        tmp_path / 'result.json',
    )
    assert command[:6] == ['uv.exe', 'run', '--project', str(tmp_path), '--frozen', 'python']
    assert command[-3:] == ['runner.py', str(tmp_path / 'request.json'), str(tmp_path / 'result.json')]
    assert working_dir == tmp_path


def test_conda_runtime_requires_prepared_environment(tmp_path, monkeypatch):
    spec = AlgorithmSpec(
        module_id='error_detection',
        algorithm_id='conda_demo',
        label='Conda Demo',
        runtime='conda',
        entrypoint='runner.py',
        manifest_path=tmp_path / 'algorithm.json',
        project_dir=tmp_path,
        environment_file=tmp_path / 'environment.yml',
    )
    monkeypatch.setattr(executor_module.shutil, 'which', lambda name: 'conda.exe')
    monkeypatch.setattr(executor_module, 'CONDA_ENVS_DIR', tmp_path / 'envs')
    with pytest.raises(AlgorithmEnvironmentError, match='尚未安装'):
        executor_module._runtime_command(
            spec,
            tmp_path / 'request.json',
            tmp_path / 'result.json',
        )


def test_subprocess_result_must_follow_algorithm_result_contract(tmp_path):
    result_path = tmp_path / 'result.json'
    result_path.write_text('{"algorithm": "broken"}', encoding='utf-8')
    with pytest.raises(AlgorithmProtocolError, match='AlgorithmResult'):
        executor_module._read_result(result_path)
