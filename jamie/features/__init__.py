# Features

from .default import RSEFeatures
from ..common.lib import arrow_table

allowed_features = {
    "rse": {"description": "Features corresponding to RSE jobs", "class": RSEFeatures}
}


def select_features(f):
    if f in allowed_features:
        return allowed_features[f]["class"]
    else:
        return None


def list_features():
    return arrow_table(
        [(k, allowed_features[k]["description"]) for k in allowed_features],
    )
