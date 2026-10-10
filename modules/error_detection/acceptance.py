from pathlib import Path

from core.acceptance import AcceptanceEvidence
from core.datasets import load_csv
from core.experiment import save_experiment
from modules.error_detection.algorithm import detect_missing


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'datasets' / 'samples' / 'errors_demo.csv'


def run_acceptance(output_dir: Path) -> AcceptanceEvidence:
    result = detect_missing(load_csv(SAMPLE))
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
