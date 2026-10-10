import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'experiments'


def save_experiment(result, dataset_id: str, config=None, output_dir=None):
    result_payload = result.to_dict()
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError('dataset_id must be a non-empty string')
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise TypeError('config must be a dictionary')

    dest = Path(output_dir) if output_dir else OUTPUT_DIR
    dest.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    record: dict[str, Any] = {
        'experiment_id': run_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'task_type': result_payload['task_type'],
        'algorithm': result_payload['algorithm'],
        'dataset_id': dataset_id,
        'config': config,
        'metrics': result_payload['metrics'],
        'metadata': result_payload['metadata'],
        'predictions': result_payload['predictions'],
    }
    try:
        serialized = json.dumps(record, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as exc:
        raise TypeError('experiment record must be JSON serializable') from exc
    file = dest / f'{run_id}.json'
    file.write_text(serialized, encoding='utf-8')
    return file
