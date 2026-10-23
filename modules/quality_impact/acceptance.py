from pathlib import Path

from core.acceptance import AcceptanceEvidence
from core.executor import execute_algorithm
from core.experiment import save_experiment


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'datasets' / 'samples' / 'quality_demo.csv'


def run_acceptance(output_dir: Path) -> AcceptanceEvidence:
    result = execute_algorithm(
        module_id='quality_impact',
        algorithm_id='missing_baseline',
        inputs={'dataset_path': str(SAMPLE)},
        params={'target': 'label', 'rate': 0.1, 'seed': 0, 'classifier': 'logreg'},
        workspace_root=output_dir / 'runs',
    )
    experiment = save_experiment(
        result,
        dataset_id='quality_demo_v1',
        config={'algorithm_id': 'missing_baseline', 'rate': 0.1, 'seed': 0, 'classifier': 'logreg'},
        output_dir=output_dir,
    )
    return AcceptanceEvidence(
        module_id='quality_impact',
        results=[result],
        experiment_files=[experiment],
        sample_files=[SAMPLE],
        metadata={'error_type': 'missing', 'conditions': 4},
    ).validate()
