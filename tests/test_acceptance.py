import json

import pytest

from core.acceptance import AcceptanceEvidence
from core.base import AlgorithmResult
from core.registry import get_module
from tools.acceptance import Check, assess_module, write_report


def test_acceptance_evidence_enforces_module_result_contract(tmp_path):
    result = AlgorithmResult('error_detection', 'baseline', []).validate()
    experiment = tmp_path / 'run.json'
    experiment.write_text('{}', encoding='utf-8')
    sample = tmp_path / 'sample.csv'
    sample.write_text('value\n1\n', encoding='utf-8')
    evidence = AcceptanceEvidence('error_detection', [result], [experiment], [sample])
    assert evidence.validate() is evidence

    with pytest.raises(ValueError, match='task_type'):
        AcceptanceEvidence('data_repair', [result], [experiment], [sample]).validate()


def test_phase3_distinguishes_real_thin_slice_from_placeholder():
    implemented = assess_module(get_module('error_detection'), phase=3)
    placeholder = assess_module(get_module('data_repair'), phase=3)
    assert implemented.ready
    assert implemented.method_count == 1
    assert not placeholder.ready
    assert any(check.name == '真实页面' and check.status == 'fail' for check in placeholder.checks)
    assert any(check.name == '验收入口' and check.status == 'fail' for check in placeholder.checks)


def test_phase4_and_phase5_have_distinct_gates():
    spec = get_module('error_detection')
    assert assess_module(spec, phase=4).ready
    final = assess_module(spec, phase=5)
    assert not final.ready
    assert any(check.name == '最终方法数量' and check.status == 'fail' for check in final.checks)


def test_acceptance_report_is_machine_and_human_readable(tmp_path):
    assessment = assess_module(get_module('error_detection'), phase=3)
    markdown, report_json = write_report(
        [assessment],
        phase=3,
        output_dir=tmp_path,
        label='unit test',
        suite_check=Check('全量回归测试', 'pass', 'tests passed'),
    )
    payload = json.loads(report_json.read_text(encoding='utf-8'))
    assert payload['gate_ready'] is True
    assert payload['summary'] == {'ready': 1, 'total': 1}
    assert '阶段 3 验收报告' in markdown.read_text(encoding='utf-8')
