from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIR = ROOT / 'runs'


@dataclass(frozen=True)
class RunWorkspace:
    run_id: str
    root: Path
    input_dir: Path
    request_path: Path
    result_path: Path
    stdout_path: Path
    stderr_path: Path


def create_run_workspace(output_root: str | Path | None = None) -> RunWorkspace:
    runs_root = (Path(output_root) if output_root is not None else DEFAULT_RUNS_DIR).resolve()
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    root = runs_root / run_id
    input_dir = root / 'input'
    input_dir.mkdir(parents=True, exist_ok=False)
    return RunWorkspace(
        run_id=run_id,
        root=root,
        input_dir=input_dir,
        request_path=root / 'request.json',
        result_path=root / 'result.json',
        stdout_path=root / 'stdout.log',
        stderr_path=root / 'stderr.log',
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    try:
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as exc:
        raise TypeError(f'Runtime payload must be JSON serializable: {path.name}') from exc
    path.write_text(serialized + '\n', encoding='utf-8')


def _safe_name(value: str, fallback: str) -> str:
    name = Path(value).name
    name = re.sub(r'[^\w.-]+', '_', name, flags=re.UNICODE).strip('._')
    return name or fallback


def materialize_inputs(inputs: dict[str, Any], workspace: RunWorkspace) -> dict[str, Any]:
    if not isinstance(inputs, dict):
        raise TypeError('inputs must be a dictionary')

    file_index = 0

    def normalize(value: Any, key: str) -> Any:
        nonlocal file_index
        if isinstance(value, Path):
            return str(value.resolve())
        if isinstance(value, str) and key.endswith(('_path', '_paths')):
            candidate = Path(value)
            if candidate.exists():
                return str(candidate.resolve())
        if hasattr(value, 'read'):
            file_index += 1
            filename = _safe_name(str(getattr(value, 'name', '')), f'{key}_{file_index}.bin')
            destination = workspace.input_dir / filename
            if destination.exists():
                destination = workspace.input_dir / f'{file_index:03d}_{filename}'
            if hasattr(value, 'seek'):
                value.seek(0)
            with destination.open('wb') as handle:
                shutil.copyfileobj(value, handle)
            if hasattr(value, 'seek'):
                value.seek(0)
            return str(destination.resolve())
        if isinstance(value, dict):
            return {str(child_key): normalize(child_value, str(child_key)) for child_key, child_value in value.items()}
        if isinstance(value, (list, tuple)):
            return [normalize(item, key) for item in value]
        return value

    normalized = {str(key): normalize(value, str(key)) for key, value in inputs.items()}
    try:
        json.dumps(normalized, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TypeError('inputs must contain paths, uploaded files, or JSON-serializable values') from exc
    return normalized
