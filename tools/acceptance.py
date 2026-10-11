from __future__ import annotations

import argparse
import ast
import importlib
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.acceptance import AcceptanceEvidence  # noqa: E402
from core.registry import MODULE_SPECS, ModuleSpec  # noqa: E402


EXPERIMENT_FIELDS = {
    'experiment_id',
    'created_at',
    'task_type',
    'algorithm',
    'dataset_id',
    'config',
    'metrics',
    'metadata',
    'predictions',
}
README_SECTIONS = ('## 方法', '## 数据', '## 运行', '## 限制')
NEGATIVE_TEST_WORDS = ('invalid', 'error', 'reject', 'empty', 'bad')
PROHIBITED_SUFFIXES = ('.pem', '.key', '.p12', '.pfx')
PLACEHOLDER_MARKERS = ('render_placeholder', '本模块尚未实现')
PROFILES = ('development', 'midterm', 'final')
PROFILE_LABELS = {
    'development': '开发自查',
    'midterm': '中期提交检查',
    'final': '最终提交检查',
}
PROFILE_RANK = {profile: rank for rank, profile in enumerate(PROFILES, start=1)}


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


@dataclass
class ModuleAssessment:
    module_id: str
    label: str
    profile: str
    ready: bool
    method_count: int
    runtime_seconds: float | None
    checks: list[Check]


def _check(name: str, condition: bool, success: str, failure: str) -> Check:
    return Check(name, 'pass' if condition else 'fail', success if condition else failure)


def _review(name: str, detail: str) -> Check:
    return Check(name, 'review', detail)


def _test_names(test_file: Path) -> list[str]:
    if not test_file.is_file():
        return []
    tree = ast.parse(test_file.read_text(encoding='utf-8'), filename=str(test_file))
    return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')]


def _page_check(spec: ModuleSpec) -> Check:
    try:
        renderer = spec.load_page()
    except Exception as exc:  # pragma: no cover - exact import errors depend on student code
        return Check('页面入口', 'fail', f'导入失败：{type(exc).__name__}: {exc}')
    return _check('页面入口', callable(renderer), 'render() 可导入并调用', '页面入口不是可调用对象')


def _experiment_checks(evidence: AcceptanceEvidence) -> list[Check]:
    checks: list[Check] = []
    result_methods = {result.algorithm for result in evidence.results}
    for path in evidence.experiment_files:
        if not path.is_file():
            checks.append(Check('实验 JSON', 'fail', f'文件不存在：{path}'))
            continue
        try:
            record = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            checks.append(Check('实验 JSON', 'fail', f'无法读取：{type(exc).__name__}: {exc}'))
            continue
        missing = sorted(EXPERIMENT_FIELDS - set(record))
        valid = not missing and record.get('task_type') == evidence.module_id and record.get('algorithm') in result_methods
        detail = '字段完整且与验收结果一致' if valid else f'字段或标识不一致；缺失字段：{missing}'
        checks.append(Check('实验 JSON', 'pass' if valid else 'fail', detail))
    return checks


def _safe_file_check(module_dir: Path, evidence: AcceptanceEvidence | None) -> Check:
    candidates = [path for path in module_dir.rglob('*') if path.is_file() and '__pycache__' not in path.parts]
    if evidence:
        candidates.extend(evidence.sample_files)
    unsafe = []
    for path in candidates:
        if path.name == '.env' or path.suffix.lower() in PROHIBITED_SUFFIXES:
            unsafe.append(str(path))
        elif path.stat().st_size > 10 * 1024 * 1024:
            unsafe.append(f'{path} (>10 MB)')
    return _check('文件安全与大小', not unsafe, '未发现密钥文件或超过 10 MB 的组内文件', f'需处理：{unsafe}')


def assess_module(spec: ModuleSpec, profile: str) -> ModuleAssessment:
    if profile not in PROFILE_RANK:
        raise ValueError(f'Unknown acceptance profile: {profile}')
    module_dir = ROOT / 'modules' / spec.module_id
    page_file = module_dir / 'page.py'
    algorithm_file = module_dir / 'algorithm.py'
    readme_file = module_dir / 'README.md'
    test_file = module_dir / f'test_{spec.module_id}.py'
    dataset_card = module_dir / 'DATASET_CARD.md'
    checks: list[Check] = []

    checks.append(_check('模块目录', module_dir.is_dir(), '目录存在', f'缺少 {module_dir.relative_to(ROOT)}'))
    checks.append(_page_check(spec))
    page_text = page_file.read_text(encoding='utf-8') if page_file.is_file() else ''
    is_placeholder = any(marker in page_text for marker in PLACEHOLDER_MARKERS)
    checks.append(_check('真实页面', bool(page_text) and not is_placeholder, '页面已脱离占位实现', '仍在使用占位页面'))
    checks.append(_check('算法文件', algorithm_file.is_file(), 'algorithm.py 存在', '缺少 algorithm.py'))

    readme_text = readme_file.read_text(encoding='utf-8') if readme_file.is_file() else ''
    missing_sections = [section for section in README_SECTIONS if section not in readme_text]
    checks.append(_check('模块 README', not missing_sections, '方法、数据、运行和限制说明完整', f'缺少 README 小节：{missing_sections}'))

    test_names = _test_names(test_file)
    has_negative = any(any(word in name.lower() for word in NEGATIVE_TEST_WORDS) for name in test_names)
    checks.append(_check('正常与错误测试', len(test_names) >= 2 and has_negative, f'发现 {len(test_names)} 个测试并包含错误输入案例', f'发现 {len(test_names)} 个测试；需至少 2 个且包含错误输入案例'))

    evidence: AcceptanceEvidence | None = None
    runtime: float | None = None
    hook_name = f'modules.{spec.module_id}.acceptance'
    try:
        hook = importlib.import_module(hook_name).run_acceptance
        with tempfile.TemporaryDirectory(prefix=f'databench-{spec.module_id}-') as temp_dir:
            started = time.perf_counter()
            evidence = hook(Path(temp_dir))
            runtime = time.perf_counter() - started
            if not isinstance(evidence, AcceptanceEvidence):
                raise TypeError('run_acceptance must return AcceptanceEvidence')
            evidence.validate()
            checks.append(Check('验收入口', 'pass', 'run_acceptance() 返回有效证据'))
            checks.append(_check('模块标识', evidence.module_id == spec.module_id, '结果 task_type 与模块 ID 一致', '证据 module_id 不匹配'))
            samples_ok = all(path.is_file() and path.stat().st_size <= 10 * 1024 * 1024 for path in evidence.sample_files)
            checks.append(_check('小型样例', samples_ok, f'{len(evidence.sample_files)} 个样例文件可用', '样例不存在或超过 10 MB'))
            checks.append(_check('运行时间', runtime <= 10.0, f'验收运行耗时 {runtime:.3f}s', f'验收运行耗时 {runtime:.3f}s，超过 10s'))
            checks.extend(_experiment_checks(evidence))
    except Exception as exc:
        checks.append(Check('验收入口', 'fail', f'{type(exc).__name__}: {exc}'))

    method_count = len({result.algorithm for result in evidence.results}) if evidence else 0
    checks.append(_safe_file_check(module_dir, evidence))
    checks.append(_review('页面语义检查', '人工确认页面展示输入、参数、结果和可理解的错误信息'))
    checks.append(_review('数据合规检查', '人工确认数据来源、许可、标签或真值说明准确且不含敏感信息'))

    if PROFILE_RANK[profile] >= PROFILE_RANK['midterm']:
        has_contract = any('contract' in name.lower() for name in test_names)
        has_experiment = any('experiment' in name.lower() for name in test_names)
        checks.append(_check('中期测试覆盖', len(test_names) >= 4 and has_contract and has_experiment, '至少 4 个测试并覆盖结果合同和实验记录', '需至少 4 个测试，并包含 contract 和 experiment 测试'))
        checks.append(_check('中期方法数量', method_count >= 1, f'可运行方法数：{method_count}', '至少需要 1 种可运行基础方法'))

    if PROFILE_RANK[profile] >= PROFILE_RANK['final']:
        checks.append(_check('最终方法数量', method_count >= 2, f'可运行方法数：{method_count}', f'仅发现 {method_count} 种方法，最终验收至少需要 2 种'))
        checks.append(_check('数据集卡', dataset_card.is_file(), '模块数据集卡存在', '缺少 modules/<module_id>/DATASET_CARD.md'))
        final_sections = ('失败案例', '指标')
        missing_final = [section for section in final_sections if section not in readme_text]
        checks.append(_check('最终实验说明', not missing_final, '包含指标和失败案例说明', f'README 缺少关键词：{missing_final}'))

    ready = not any(check.status == 'fail' for check in checks)
    return ModuleAssessment(spec.module_id, spec.label, profile, ready, method_count, runtime, checks)


def run_test_suite() -> Check:
    with tempfile.TemporaryDirectory(prefix='databench-pytest-', dir=ROOT) as base_temp:
        completed = subprocess.run(
            [sys.executable, '-m', 'pytest', '-q', '--basetemp', base_temp],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    output = '\n'.join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    tail = '\n'.join(output.splitlines()[-3:]) if output else 'pytest 未产生输出'
    return Check('全量回归测试', 'pass' if completed.returncode == 0 else 'fail', tail)


def _slug(label: str) -> str:
    safe = ''.join(char.lower() if char.isalnum() else '_' for char in label.strip())
    return '_'.join(filter(None, safe.split('_'))) or 'current'


def write_report(
    assessments: Iterable[ModuleAssessment],
    profile: str,
    output_dir: Path,
    label: str,
    suite_check: Check,
) -> tuple[Path, Path]:
    if profile not in PROFILE_LABELS:
        raise ValueError(f'Unknown acceptance profile: {profile}')
    assessments = list(assessments)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f'{profile}_{_slug(label)}'
    json_path = output_dir / f'{stem}.json'
    markdown_path = output_dir / f'{stem}.md'
    ready_count = sum(item.ready for item in assessments)
    gate_ready = ready_count == len(assessments) and suite_check.status == 'pass'
    payload = {
        'schema_version': 1,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'profile': profile,
        'label': label,
        'gate_ready': gate_ready,
        'summary': {'ready': ready_count, 'total': len(assessments)},
        'global_checks': [asdict(suite_check)],
        'modules': [asdict(item) for item in assessments],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    lines = [
        f'# {PROFILE_LABELS[profile]}报告：{label}',
        '',
        f'- 生成时间（UTC）：`{payload["generated_at"]}`',
        f'- 自动门禁：`{"PASS" if gate_ready else "BLOCKED"}`',
        f'- 模块就绪：`{ready_count}/{len(assessments)}`',
        f'- 全量测试：`{suite_check.status.upper()}` — {suite_check.detail.replace(chr(10), "；")}',
        '',
        '| 模块 | 状态 | 方法数 | 验收耗时 |',
        '| --- | --- | ---: | ---: |',
    ]
    for item in assessments:
        runtime = '-' if item.runtime_seconds is None else f'{item.runtime_seconds:.3f}s'
        lines.append(f'| `{item.module_id}` | {"PASS" if item.ready else "BLOCKED"} | {item.method_count} | {runtime} |')
    for item in assessments:
        lines.extend(['', f'## {item.label}', ''])
        for check in item.checks:
            icon = {'pass': '✅', 'fail': '❌', 'review': '🔎'}[check.status]
            lines.append(f'- {icon} **{check.name}**：{check.detail}')
    lines.extend([
        '',
        '## 判定说明',
        '',
        '- `PASS` 表示自动检查无失败项；`BLOCKED` 表示至少一项机器检查失败。',
        '- 🔎 项需要研究生人工复核，不会被工具静默认定为通过。',
        '- 检查全部模块时，只有 8 个模块和全量测试都通过，整体门禁才通过。',
    ])
    markdown_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return markdown_path, json_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run DataBench development and submission checks.')
    parser.add_argument('--profile', choices=PROFILES, required=True, help='Check profile: development, midterm, or final.')
    parser.add_argument('--module', choices=[spec.module_id for spec in MODULE_SPECS])
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'reports' / 'acceptance')
    parser.add_argument('--label', default='current')
    parser.add_argument('--skip-tests', action='store_true', help='Skip the global pytest run (never use for a release decision).')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = args.profile
    specs = [spec for spec in MODULE_SPECS if args.module in (None, spec.module_id)]
    assessments = [assess_module(spec, profile) for spec in specs]
    suite_check = Check('全量回归测试', 'review', '按命令参数跳过') if args.skip_tests else run_test_suite()
    markdown, report_json = write_report(assessments, profile, args.output_dir, args.label, suite_check)
    ready = all(item.ready for item in assessments) and suite_check.status == 'pass'
    print(f'CHECK_{profile.upper()}={"PASS" if ready else "BLOCKED"}')
    print(f'MARKDOWN={markdown}')
    print(f'JSON={report_json}')
    return 0 if ready else 1


if __name__ == '__main__':
    raise SystemExit(main())
