from pathlib import Path
import pandas as pd


def read_list(fn):
    return list(filter(None, map(str.strip, Path(fn).read_text().split("\n"))))


EMPLOYERS = read_list(Path(__file__).parent / "uk_uni_list.txt")
POSTCODES = pd.read_csv(Path(__file__).parent / "uk_uni_postcode.csv")
