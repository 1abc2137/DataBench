from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    '01_error_detection.md': 'error_detection',
    '02_data_repair.md': 'data_repair',
    '03_quality_impact.md': 'quality_impact',
    '04_dependency_discovery.md': 'dependency_discovery',
    '05_truth_discovery.md': 'truth_discovery',
    '06_entity_matching.md': 'entity_matching',
    '07_table_discovery.md': 'table_discovery',
    '08_query_analysis.md': 'query_analysis',
}


def test_student_release_materials_are_complete():
    assert (ROOT / 'VERSION').read_text(encoding='utf-8').strip() == '0.4.1'
    for required in (
        'docs/STUDENT_RELEASE_GUIDE.md',
        'docs/MINIMUM_PLAN_TEMPLATE.md',
        'docs/DATASET_CARD_TEMPLATE.md',
        'docs/SUBMISSION_CHECKLIST.md',
        'docs/STUDENT_RELEASE_NOTES_v0.4.1.md',
        'docs/ACCEPTANCE_GUIDE.md',
        'docs/TESTING_GUIDE.md',
    ):
        assert (ROOT / required).is_file(), required

    for filename, module_id in TASKS.items():
        text = (ROOT / 'docs' / 'tasks' / filename).read_text(encoding='utf-8')
        assert f'`{module_id}`' in text
        assert '## 两种' in text
        assert '## 第一阶段数据集' in text
        assert '## 评价' in text
        assert '## 不做事项' in text

def test_issue_templates_capture_required_information():
    bug = (ROOT / '.github/ISSUE_TEMPLATE/bug_report.md').read_text(encoding='utf-8')
    for heading in ('## 环境', '## 最小复现步骤', '## 预期结果', '## 实际结果', '## 完整日志'):
        assert heading in bug

    interface = (ROOT / '.github/ISSUE_TEMPLATE/interface_change.md').read_text(encoding='utf-8')
    for heading in ('## 当前接口', '## 期望接口', '## 复用范围', '## 兼容性影响', '## 测试和迁移方案'):
        assert heading in interface
