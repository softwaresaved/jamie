import json
import pytest
from pathlib import Path
from jamie.scrape import JobFile

TEST_INPUT_FOLDER = Path("test-input")


def _corresponding_json(f: Path) -> Path:
    return f.parent / (f.stem + ".json")


# HTML files collected by the scraper do not have an extension
# Only keep files which have corresponding metadata
if TEST_INPUT_FOLDER.exists():
    FILES = [
        (f, _corresponding_json(f))
        for f in TEST_INPUT_FOLDER.glob("*")
        if f.suffix == "" and _corresponding_json(f).exists()
    ]
else:
    FILES = []


@pytest.mark.parametrize("filename,expected_json", FILES)
def test_parser(filename, expected_json):
    with expected_json.open() as fp:
        data = json.load(fp)
    assert JobFile(filename).parse().json == data
