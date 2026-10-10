from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.base import AlgorithmResult


@dataclass
class AcceptanceEvidence:
    """Machine-checkable evidence returned by a module acceptance smoke run."""

    module_id: str
    results: list[AlgorithmResult]
    experiment_files: list[Path]
    sample_files: list[Path]
    metadata: dict = field(default_factory=dict)

    def validate(self) -> 'AcceptanceEvidence':
        if not isinstance(self.module_id, str) or not self.module_id.strip():
            raise ValueError('module_id must be a non-empty string')
        if not isinstance(self.results, list) or not self.results:
            raise ValueError('results must contain at least one AlgorithmResult')
        for result in self.results:
            if not isinstance(result, AlgorithmResult):
                raise TypeError('results must contain only AlgorithmResult objects')
            result.validate()
            if result.task_type != self.module_id:
                raise ValueError(
                    f'result task_type {result.task_type!r} does not match module_id {self.module_id!r}'
                )
        if not isinstance(self.experiment_files, list) or not self.experiment_files:
            raise ValueError('experiment_files must contain at least one path')
        if not isinstance(self.sample_files, list) or not self.sample_files:
            raise ValueError('sample_files must contain at least one path')
        if not all(isinstance(path, Path) for path in self.experiment_files):
            raise TypeError('experiment_files must contain pathlib.Path objects')
        if not all(isinstance(path, Path) for path in self.sample_files):
            raise TypeError('sample_files must contain pathlib.Path objects')
        if not isinstance(self.metadata, dict):
            raise TypeError('metadata must be a dictionary')
        return self
