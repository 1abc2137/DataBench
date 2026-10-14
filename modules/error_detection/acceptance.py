from pathlib import Path

from core.acceptance import AcceptanceEvidence
from core.executor import execute_algorithm
from core.experiment import save_experiment


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'datasets' / 'samples' / 'errors_demo.csv'


def run_acceptance(output_dir: Path) -> AcceptanceEvidence:
    result = execute_algorithm(
        module_id='error_detection',
        algorithm_id='missing_value_baseline',
        inputs={'dataset_path': SAMPLE},
        params={},
        workspace_root=output_dir / 'runs',
    )
    experiment = save_experiment(
        result,
        dataset_id='errors_demo_v1',
        config={'method': 'missing_value_baseline'},
        output_dir=output_dir,
    )
    return AcceptanceEvidence(
        module_id='error_detection',
        results=[result],
        experiment_files=[experiment],
        sample_files=[SAMPLE],
        metadata={'expected_missing_cells': 2},
    ).validate()
