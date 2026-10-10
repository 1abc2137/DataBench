from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
RELEASE_DIR = ROOT / 'release'
ARCHIVE_ROOT = f'DataBench_Starter_v{VERSION}'

TOP_LEVEL_FILES = (
    '.gitignore',
    'app.py',
    'CHANGELOG.md',
    'README.md',
    'requirements.txt',
    'VERSION',
)
DIRECTORIES = (
    '.github',
    'core',
    'datasets/samples',
    'modules',
    'tests',
    'tools',
)
DOCUMENTS = (
    'docs/ACCEPTANCE_GUIDE.md',
    'docs/DATASET_CARD_TEMPLATE.md',
    'docs/MINIMUM_PLAN_TEMPLATE.md',
    'docs/MODULE_SPEC.md',
    'docs/STUDENT_MODULE_TEMPLATE.md',
    'docs/STUDENT_RELEASE_GUIDE.md',
    f'docs/STUDENT_RELEASE_NOTES_v{VERSION}.md',
    'docs/SUBMISSION_CHECKLIST.md',
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def include_file(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in {'.venv', '.pytest_cache', '__pycache__', 'experiments', 'release'} for part in relative.parts):
        return False
    return path.is_file() and path.suffix not in {'.pyc', '.pyo'}


def collect_files() -> list[Path]:
    files = [ROOT / name for name in TOP_LEVEL_FILES]
    files.extend(ROOT / name for name in DOCUMENTS)
    files.extend((ROOT / 'docs' / 'tasks').rglob('*'))
    for directory in DIRECTORIES:
        files.extend((ROOT / directory).rglob('*'))

    selected = sorted({path.resolve() for path in files if include_file(path)}, key=lambda path: path.as_posix())
    missing = [path for path in (ROOT / name for name in (*TOP_LEVEL_FILES, *DOCUMENTS)) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f'Missing release files: {missing}')
    return selected


def build() -> tuple[Path, Path, Path]:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    archive = RELEASE_DIR / f'DataBench_Starter_v{VERSION}_student.zip'
    manifest = RELEASE_DIR / f'DataBench_Starter_v{VERSION}_manifest.txt'
    checksum = archive.with_suffix(archive.suffix + '.sha256')
    files = collect_files()

    manifest_lines = []
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            archive_name = f'{ARCHIVE_ROOT}/{relative}'
            package.write(path, archive_name)
            manifest_lines.append(f'{sha256(path)}  {archive_name}')

    manifest.write_text('\n'.join(manifest_lines) + '\n', encoding='utf-8')
    checksum.write_text(f'{sha256(archive)}  {archive.name}\n', encoding='utf-8')
    return archive, checksum, manifest


if __name__ == '__main__':
    for artifact in build():
        print(artifact)
