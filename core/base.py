import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AlgorithmResult:
    task_type: str
    algorithm: str
    predictions: Any
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        if not isinstance(self.task_type, str) or not self.task_type.strip():
            raise ValueError('task_type must be a non-empty string')
        if not isinstance(self.algorithm, str) or not self.algorithm.strip():
            raise ValueError('algorithm must be a non-empty string')
        if self.predictions is None:
            raise ValueError('predictions is required and cannot be None')
        if not isinstance(self.metrics, dict):
            raise TypeError('metrics must be a dictionary')
        if not isinstance(self.metadata, dict):
            raise TypeError('metadata must be a dictionary')

        payload = {
            'task_type': self.task_type,
            'algorithm': self.algorithm,
            'predictions': self.predictions,
            'metrics': self.metrics,
            'metadata': self.metadata,
        }
        try:
            json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise TypeError('AlgorithmResult fields must be JSON serializable') from exc
        return payload

    def validate(self) -> 'AlgorithmResult':
        self.to_dict()
        return self
