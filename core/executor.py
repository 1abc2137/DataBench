from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from core.algorithm_registry import AlgorithmSpec, ROOT, get_algorithm
from core.base import AlgorithmResult
from core.run_workspace import create_run_workspace, materialize_inputs, write_json
from core.runtime_errors import (
    AlgorithmEnvironmentError,
    AlgorithmExecutionError,
    AlgorithmProtocolError,
)


CONDA_ENVS_DIR = ROOT / '.algorithm_envs'


def _load_callable(entrypoint: str):
    try:
        module_name, function_name = entrypoint.split(':', maxsplit=1)
        function = getattr(importlib.import_module(module_name), function_name)
    except (ValueError, ImportError, AttributeError) as exc:
        raise AlgorithmProtocolError(f'Cannot load builtin entrypoint: {entrypoint}') from exc
    if not callable(function):
        raise AlgorithmProtocolError(f'Builtin entrypoint is not callable: {entrypoint}')
    return function


def _runtime_command(spec: AlgorithmSpec, request_path: Path, result_path: Path) -> tuple[list[str], Path]:
    if spec.runtime == 'uv':
        uv = shutil.which('uv')
        if uv is None:
            raise AlgorithmEnvironmentError('找不到 uv，请先安装 uv 并重新打开终端。')
        command = [
            uv,
            'run',
            '--project',
            str(spec.project_dir),
            '--frozen',
            'python',
            spec.entrypoint,
            str(request_path),
            str(result_path),
        ]
        return command, spec.project_dir

    if spec.runtime == 'conda':
        conda = shutil.which('conda')
        if conda is None:
            raise AlgorithmEnvironmentError('找不到 conda，无法运行该算法。')
        prefix = CONDA_ENVS_DIR / f'{spec.module_id}--{spec.algorithm_id}'
        if not prefix.is_dir():
            raise AlgorithmEnvironmentError(
                f'算法环境尚未安装，请运行：uv run python tools/algorithm_env.py sync '
                f'{spec.module_id} {spec.algorithm_id}'
            )
        command = [
            conda,
            'run',
            '--prefix',
            str(prefix),
            'python',
            spec.entrypoint,
            str(request_path),
            str(result_path),
        ]
        return command, spec.project_dir

    raise AlgorithmProtocolError(f'Runtime does not use a subprocess: {spec.runtime}')


def _run_subprocess(spec: AlgorithmSpec, request_path: Path, result_path: Path) -> tuple[str, str]:
    command, working_dir = _runtime_command(spec, request_path, result_path)
    environment = os.environ.copy()
    environment.setdefault('UV_CACHE_DIR', str(ROOT / '.uv-cache'))
    try:
        completed = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            check=False,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise AlgorithmExecutionError(
            f'算法 {spec.label} 运行超过 {spec.timeout_seconds} 秒，已终止。'
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or '未提供错误日志'
        raise AlgorithmExecutionError(
            f'算法 {spec.label} 运行失败（退出码 {completed.returncode}）：{detail}'
        )
    return completed.stdout, completed.stderr


def _read_result(path: Path) -> AlgorithmResult:
    if not path.is_file():
        raise AlgorithmProtocolError('算法没有生成 result.json。')
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
        result = AlgorithmResult(**payload).validate()
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AlgorithmProtocolError(f'算法返回结果不符合 AlgorithmResult 合同：{exc}') from exc
    return result


def execute_algorithm(
    module_id: str,
    algorithm_id: str,
    inputs: dict[str, Any],
    params: dict[str, Any] | None = None,
    workspace_root: str | Path | None = None,
) -> AlgorithmResult:
    spec = get_algorithm(module_id, algorithm_id)
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise TypeError('params must be a dictionary')

    workspace = create_run_workspace(workspace_root)
    normalized_inputs = materialize_inputs(inputs, workspace)
    request = {
        'schema_version': 1,
        'run_id': workspace.run_id,
        'module_id': module_id,
        'algorithm_id': algorithm_id,
        'inputs': normalized_inputs,
        'params': params,
    }
    write_json(workspace.request_path, request)
    started = time.perf_counter()

    if spec.runtime == 'builtin':
        function = _load_callable(spec.entrypoint)
        try:
            result = function(normalized_inputs, params)
        except Exception as exc:
            workspace.stderr_path.write_text(f'{type(exc).__name__}: {exc}\n', encoding='utf-8')
            raise AlgorithmExecutionError(f'算法 {spec.label} 运行失败：{exc}') from exc
        if not isinstance(result, AlgorithmResult):
            raise AlgorithmProtocolError('builtin 算法必须返回 AlgorithmResult。')
        result.validate()
        write_json(workspace.result_path, result.to_dict())
        stdout = ''
        stderr = ''
    else:
        stdout, stderr = _run_subprocess(spec, workspace.request_path, workspace.result_path)
        result = _read_result(workspace.result_path)

    workspace.stdout_path.write_text(stdout, encoding='utf-8')
    workspace.stderr_path.write_text(stderr, encoding='utf-8')
    elapsed = time.perf_counter() - started
    result.metadata.setdefault('runtime', spec.runtime)
    result.metadata.setdefault('runtime_seconds', round(elapsed, 6))
    result.metadata.setdefault('run_id', workspace.run_id)
    result.metadata.setdefault('run_directory', str(workspace.root.resolve()))
    result.validate()
    write_json(workspace.result_path, result.to_dict())
    return result
