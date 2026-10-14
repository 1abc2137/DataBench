"""Copyable runner template for an isolated uv or Conda algorithm project."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def run_algorithm(inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    """Replace this body with the real algorithm and return plain JSON values."""
    dataset_path = inputs['dataset_path']
    return {
        'task_type': '<module_id>',
        'algorithm': '<algorithm_id>',
        'predictions': [],
        'metrics': {},
        'metadata': {'dataset_path': dataset_path, 'params': params},
    }


def main(request_path: str, result_path: str) -> None:
    request = json.loads(Path(request_path).read_text(encoding='utf-8'))
    if request.get('schema_version') != 1:
        raise ValueError('Unsupported request schema_version')
    result = run_algorithm(request['inputs'], request['params'])
    Path(result_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python runner.py REQUEST_JSON RESULT_JSON')
    main(sys.argv[1], sys.argv[2])
