import re
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_COLLECTION_FILES = 100
MAX_COLLECTION_BYTES = 50 * 1024 * 1024


def _source_size(path_or_file):
    if isinstance(path_or_file, (str, Path)):
        return Path(path_or_file).stat().st_size
    if hasattr(path_or_file, 'size'):
        return int(path_or_file.size)
    if hasattr(path_or_file, 'getbuffer'):
        return int(path_or_file.getbuffer().nbytes)
    return None


def _source_name(path_or_file) -> str:
    if isinstance(path_or_file, (str, Path)):
        return Path(path_or_file).name
    name = getattr(path_or_file, 'name', None)
    if not name:
        raise ValueError('Each file-like object in a collection must have a name')
    return Path(str(name)).name


def _normalize_table_id(value: str) -> str:
    normalized = unicodedata.normalize('NFKC', str(value)).strip()
    normalized = re.sub(r'\s+', '_', normalized)
    normalized = re.sub(r'[^\w.-]+', '_', normalized, flags=re.UNICODE).strip('._')
    if not normalized:
        raise ValueError('table_id cannot be empty after normalization')
    return normalized


def load_csv(path_or_file) -> pd.DataFrame:
    size = _source_size(path_or_file)
    if size is not None and size > MAX_FILE_BYTES:
        raise ValueError('CSV exceeds 10 MB demo limit')
    if not isinstance(path_or_file, (str, Path)) and hasattr(path_or_file, 'seek'):
        path_or_file.seek(0)
    df = pd.read_csv(path_or_file, dtype=str, keep_default_na=False)
    if df.empty:
        raise ValueError('CSV must contain at least one data row')
    if '__row_id' in df.columns:
        raise ValueError('Reserved column name: __row_id')
    df.insert(0, '__row_id', [str(i) for i in range(len(df))])
    return df


def load_csv_collection(sources) -> dict[str, pd.DataFrame]:
    """Load a named collection of CSV files with stable table IDs.

    `sources` may be a mapping of explicit table_id to source, or an iterable
    of paths/file-like objects whose filename stems become table IDs.
    """
    if isinstance(sources, Mapping):
        items = [(_normalize_table_id(table_id), source) for table_id, source in sources.items()]
    else:
        if isinstance(sources, (str, Path)) or hasattr(sources, 'read'):
            raise TypeError('sources must be a mapping or an iterable of CSV sources')
        if not isinstance(sources, Iterable):
            raise TypeError('sources must be a mapping or an iterable of CSV sources')
        items = []
        for source in sources:
            table_id = _normalize_table_id(Path(_source_name(source)).stem)
            items.append((table_id, source))

    if not items:
        raise ValueError('At least one CSV source is required')
    if len(items) > MAX_COLLECTION_FILES:
        raise ValueError(f'CSV collection exceeds {MAX_COLLECTION_FILES} file limit')

    table_ids = [table_id for table_id, _ in items]
    if len(table_ids) != len(set(table_ids)):
        raise ValueError('Duplicate table_id in CSV collection; provide explicit unique IDs')

    known_sizes = [_source_size(source) for _, source in items]
    total_size = sum(size for size in known_sizes if size is not None)
    if total_size > MAX_COLLECTION_BYTES:
        raise ValueError('CSV collection exceeds 50 MB demo limit')

    return {table_id: load_csv(source) for table_id, source in items}
