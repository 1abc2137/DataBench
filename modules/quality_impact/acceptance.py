from pathlib import Path

from core.acceptance import AcceptanceEvidence
from core.executor import execute_algorithm
from core.experiment import save_experiment


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'datasets' / 'samples' / 'quality_demo.csv'

RUNS = [
    {'algorithm_id': 'missing_baseline', 'error_type': 'missing'},
    {'algorithm_id': 'outlier_impact', 'error_type': 'outlier'},
]


def run_acceptance(output_dir: Path) -> AcceptanceEvidence:
    """验收冒烟：跑两个算法（缺失 + 离群），各存一份实验 JSON，覆盖 final 的「≥2 方法」要求。"""
    results = []
    experiment_files = []
    for spec in RUNS:
        result = execute_algorithm(
            module_id='quality_impact',
            algorithm_id=spec['algorithm_id'],
            inputs={'dataset_path': str(SAMPLE)},
            params={'target': 'label', 'rate': 0.1, 'seed': 0, 'classifier': 'logreg'},
            workspace_root=output_dir / 'runs',
        )
        experiment = save_experiment(
            result,
            dataset_id='quality_demo_v1',
            config={'algorithm_id': spec['algorithm_id'], 'rate': 0.1, 'seed': 0, 'classifier': 'logreg'},
            output_dir=output_dir,
        )
        results.append(result)
        experiment_files.append(experiment)
    return AcceptanceEvidence(
        module_id='quality_impact',
        results=results,
        experiment_files=experiment_files,
        sample_files=[SAMPLE],
        metadata={'error_types': ['missing', 'outlier'], 'conditions': 6},
    ).validate()
