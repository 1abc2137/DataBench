from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from core.registry import get_module
from core.runtime_errors import AlgorithmConfigurationError


ROOT = Path(__file__).resolve().parents[1]
ALGORITHM_ID_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
SUPPORTED_RUNTIMES = {'builtin', 'uv', 'conda'}


@dataclass(frozen=True)
class AlgorithmSpec:
    module_id: str
    algorithm_id: str
    label: str
    runtime: str
    entrypoint: str
    manifest_path: Path
    project_dir: Path | None = None
    environment_file: Path | None = None
    timeout_seconds: int = 300

    @property
    def algorithm_dir(self) -> Path:
        return self.manifest_path.parent


def _resolve_repo_path(value: str, field_name: str, manifest_path: Path) -> Path:
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise AlgorithmConfigurationError(
            f'{field_name} must stay inside the repository: {manifest_path}'
        ) from exc
    return candidate


def _load_manifest(manifest_path: Path) -> AlgorithmSpec:
    try:
        payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise AlgorithmConfigurationError(f'Cannot read algorithm manifest: {manifest_path}') from exc
    if not isinstance(payload, dict):
        raise AlgorithmConfigurationError(f'Algorithm manifest must be a JSON object: {manifest_path}')

    required = ('module_id', 'algorithm_id', 'label', 'runtime', 'entrypoint')
    missing = [key for key in required if not isinstance(payload.get(key), str) or not payload[key].strip()]
    if missing:
        raise AlgorithmConfigurationError(f'Missing manifest fields {missing}: {manifest_path}')

    module_id = payload['module_id'].strip()
    algorithm_id = payload['algorithm_id'].strip()
    runtime = payload['runtime'].strip()
    get_module(module_id)
    expected_module_id = manifest_path.parents[2].name
    expected_algorithm_id = manifest_path.parent.name
    if module_id != expected_module_id:
        raise AlgorithmConfigurationError(
            f'module_id must match its module directory {expected_module_id!r}: {manifest_path}'
        )
    if not ALGORITHM_ID_PATTERN.fullmatch(algorithm_id):
        raise AlgorithmConfigurationError(f'Invalid algorithm_id {algorithm_id!r}: {manifest_path}')
    if algorithm_id != expected_algorithm_id:
        raise AlgorithmConfigurationError(
            f'algorithm_id must match its algorithm directory {expected_algorithm_id!r}: {manifest_path}'
        )
    if runtime not in SUPPORTED_RUNTIMES:
        raise AlgorithmConfigurationError(f'Unsupported runtime {runtime!r}: {manifest_path}')

    timeout_seconds = payload.get('timeout_seconds', 300)
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        raise AlgorithmConfigurationError(f'timeout_seconds must be a positive integer: {manifest_path}')

    project_dir = None
    environment_file = None
    if runtime in {'uv', 'conda'}:
        project_value = payload.get('project_dir')
        if not isinstance(project_value, str) or not project_value.strip():
            raise AlgorithmConfigurationError(f'{runtime} runtime requires project_dir: {manifest_path}')
        project_dir = _resolve_repo_path(project_value, 'project_dir', manifest_path)
        if not project_dir.is_dir():
            raise AlgorithmConfigurationError(f'project_dir does not exist: {project_dir}')
    if runtime == 'uv' and not (project_dir / 'pyproject.toml').is_file():
        raise AlgorithmConfigurationError(f'uv project is missing pyproject.toml: {project_dir}')
    if runtime == 'uv' and not (project_dir / 'uv.lock').is_file():
        raise AlgorithmConfigurationError(f'uv project is missing uv.lock: {project_dir}')
    if runtime in {'uv', 'conda'}:
        runner_path = (project_dir / payload['entrypoint']).resolve()
        try:
            runner_path.relative_to(project_dir)
        except ValueError as exc:
            raise AlgorithmConfigurationError(f'entrypoint must stay inside project_dir: {manifest_path}') from exc
        if not runner_path.is_file():
            raise AlgorithmConfigurationError(f'Runner entrypoint does not exist: {runner_path}')
    if runtime == 'conda':
        environment_value = payload.get('environment_file')
        if not isinstance(environment_value, str) or not environment_value.strip():
            raise AlgorithmConfigurationError(f'conda runtime requires environment_file: {manifest_path}')
        environment_file = _resolve_repo_path(environment_value, 'environment_file', manifest_path)
        if not environment_file.is_file():
            raise AlgorithmConfigurationError(f'Conda environment file does not exist: {environment_file}')

    return AlgorithmSpec(
        module_id=module_id,
        algorithm_id=algorithm_id,
        label=payload['label'].strip(),
        runtime=runtime,
        entrypoint=payload['entrypoint'].strip(),
        manifest_path=manifest_path,
        project_dir=project_dir,
        environment_file=environment_file,
        timeout_seconds=timeout_seconds,
    )


def discover_algorithms() -> tuple[AlgorithmSpec, ...]:
    specs = tuple(
        _load_manifest(path)
        for path in sorted((ROOT / 'modules').glob('*/algorithms/*/algorithm.json'))
    )
    identities = [(spec.module_id, spec.algorithm_id) for spec in specs]
    duplicates = sorted({identity for identity in identities if identities.count(identity) > 1})
    if duplicates:
        raise AlgorithmConfigurationError(f'Duplicate algorithm registrations: {duplicates}')
    return specs


def list_algorithms(module_id: str) -> tuple[AlgorithmSpec, ...]:
    get_module(module_id)
    return tuple(spec for spec in discover_algorithms() if spec.module_id == module_id)


def get_algorithm(module_id: str, algorithm_id: str) -> AlgorithmSpec:
    for spec in list_algorithms(module_id):
        if spec.algorithm_id == algorithm_id:
            return spec
    raise KeyError(f'Unknown algorithm: {module_id}/{algorithm_id}')
