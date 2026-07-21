from pathlib import Path

import pytest

from tools.validate_neuron_ids import load_records


@pytest.mark.parametrize(
    "duplicate_column",
    ["root_id", "source_id", "source_available"],
)
def test_duplicate_csv_headers_are_rejected_before_row_parsing(
    tmp_path: Path, duplicate_column: str
):
    path = tmp_path / "input.csv"
    path.write_text(
        f"{duplicate_column},{duplicate_column},other\n123,456,value\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=rf"CSV header contains duplicate column names: '{duplicate_column}'",
    ):
        load_records(path)


def test_unique_csv_headers_preserve_identifier_text(tmp_path: Path):
    path = tmp_path / "input.csv"
    path.write_text(
        "root_id,source_id,source_available\n"
        "000123,000123,true\n",
        encoding="utf-8",
    )

    assert load_records(path) == [
        {
            "root_id": "000123",
            "source_id": "000123",
            "source_available": "true",
        }
    ]
