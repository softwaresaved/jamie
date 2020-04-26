from pathlib import Path
import pandas as pd
from box import Box

def read_list(fn):
    lines = Path(fn).read_text().split('\n')
    return [l.strip() for l in lines if l.strip()]


# Datasets
datasets = Box({
    'uk_uni': {
        'list': read_list(Path(__file__).parent / 'uk_uni_list.txt'),
        'postcodes': pd.read_csv(Path(__file__).parent / 'uk_uni_postcode.csv')
    }
})
