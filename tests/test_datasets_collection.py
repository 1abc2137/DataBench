from pathlib import Path

import pytest

from core.datasets import load_csv_collection


def _write_csv(path: Path, value: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'id,value\n1,{value}\n', encoding='utf-8')
    return path


def test_load_csv_collection_from_iterable(tmp_path):
    first = _write_csv(tmp_path / 'query table.csv', 'a')
    second = _write_csv(tmp_path / '候选表.csv', 'b')

    tables = load_csv_collection([first, second])

    assert list(tables) == ['query_table', '候选表']
    assert all('__row_id' in table.columns for table in tables.values())
    assert tables['query_table'].iloc[0]['value'] == 'a'


def test_load_csv_collection_accepts_explicit_ids(tmp_path):
    tables = load_csv_collection({
        'left': _write_csv(tmp_path / 'source.csv', 'a'),
        'right': _write_csv(tmp_path / 'other.csv', 'b'),
    })
    assert list(tables) == ['left', 'right']


def test_load_csv_collection_rejects_empty_and_duplicate_ids(tmp_path):
    with pytest.raises(ValueError, match='At least one'):
        load_csv_collection([])

    first = _write_csv(tmp_path / 'left' / 'same.csv', 'a')
    second = _write_csv(tmp_path / 'right' / 'same.csv', 'b')
    with pytest.raises(ValueError, match='Duplicate table_id'):
        load_csv_collection([first, second])


def test_single_path_is_not_a_collection(tmp_path):
    path = _write_csv(tmp_path / 'one.csv', 'a')
    with pytest.raises(TypeError, match='mapping or an iterable'):
        load_csv_collection(path)
