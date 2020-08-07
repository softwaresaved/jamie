from pathlib import Path
import pandas as pd
from box import Box
from ..lib import table


def read_list(fn):
    lines = Path(fn).read_text().split("\n")
    return [line.strip() for line in lines if line.strip()]


# Employer data
employers = Box(
    {
        "uk_uni": {
            "description": "Universities in the United Kingdom",
            "list": read_list(Path(__file__).parent / "uk_uni_list.txt"),
            "postcodes": pd.read_csv(Path(__file__).parent / "uk_uni_postcode.csv"),
        }
    }
)


def list_employers():
    return table(
        [(x, employers[x]["description"]) for x in sorted(employers)],
        align="rl",
        sep="⯈",
    )


def valid_employer(e):
    return e in employers
