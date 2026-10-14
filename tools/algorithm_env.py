from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.algorithm_registry import discover_algorithms, get_algorithm  # noqa: E402
from core.executor import CONDA_ENVS_DIR  # noqa: E402


def _runtime_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.setdefault('UV_CACHE_DIR', str(ROOT / '.uv-cache'))
    return environment


def _tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f'找不到 {name}，请先安装并重新打开终端。')
    return executable


def _installed(spec) -> bool:
    if spec.runtime == 'builtin':
        return True
    if spec.runtime == 'uv':
        return (spec.project_dir / '.venv').is_dir()
    return (CONDA_ENVS_DIR / f'{spec.module_id}--{spec.algorithm_id}').is_dir()


def list_specs() -> int:
    for spec in discover_algorithms():
        state = 'installed' if _installed(spec) else 'not-installed'
        print(f'{spec.module_id}/{spec.algorithm_id}\t{spec.runtime}\t{state}\t{spec.label}')
    return 0


def sync_spec(module_id: str, algorithm_id: str) -> int:
    spec = get_algorithm(module_id, algorithm_id)
    if spec.runtime == 'builtin':
        print(f'{module_id}/{algorithm_id} 使用公共前端环境，无需额外安装。')
        return 0
    if spec.runtime == 'uv':
        command = [_tool('uv'), 'sync', '--project', str(spec.project_dir), '--frozen']
    else:
        prefix = CONDA_ENVS_DIR / f'{module_id}--{algorithm_id}'
        prefix.parent.mkdir(parents=True, exist_ok=True)
        action = 'update' if prefix.is_dir() else 'create'
        command = [
            _tool('conda'),
            'env',
            action,
            '--prefix',
            str(prefix),
            '--file',
            str(spec.environment_file),
        ]
        if action == 'update':
            command.append('--prune')
    return subprocess.run(command, cwd=ROOT, check=False, env=_runtime_environment()).returncode


def check_spec(module_id: str, algorithm_id: str) -> int:
    spec = get_algorithm(module_id, algorithm_id)
    if not _installed(spec):
        print(f'未安装：{module_id}/{algorithm_id}', file=sys.stderr)
        return 1
    if spec.runtime == 'builtin':
        print(f'可用：{module_id}/{algorithm_id}（公共前端环境）')
        return 0
    if spec.runtime == 'uv':
        command = [
            _tool('uv'), 'run', '--project', str(spec.project_dir), '--frozen',
            'python', '-c', 'import sys; print(sys.version)',
        ]
    else:
        prefix = CONDA_ENVS_DIR / f'{module_id}--{algorithm_id}'
        command = [
            _tool('conda'), 'run', '--prefix', str(prefix),
            'python', '-c', 'import sys; print(sys.version)',
        ]
    return subprocess.run(command, cwd=ROOT, check=False, env=_runtime_environment()).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description='管理 DataBench 算法运行环境')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('list', help='列出算法及环境状态')
    for command in ('sync', 'check'):
        subparser = subparsers.add_parser(command)
        subparser.add_argument('module_id')
        subparser.add_argument('algorithm_id')
    args = parser.parse_args()
    if args.command == 'list':
        return list_specs()
    if args.command == 'sync':
        return sync_spec(args.module_id, args.algorithm_id)
    return check_spec(args.module_id, args.algorithm_id)


if __name__ == '__main__':
    raise SystemExit(main())
