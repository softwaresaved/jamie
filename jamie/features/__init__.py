# Features

from .default import RSEFeatures
from ..common.lib import table

allowed_features = {
    "rse": {"description": "Features corresponding to RSE jobs", "class": RSEFeatures}
}


def select_features(f):
    return allowed_features.get(f, None)


def list_features():
    return table(
        [(k, allowed_features[k]["description"]) for k in allowed_features],
        align="rl",
        sep="⯈",
    )
