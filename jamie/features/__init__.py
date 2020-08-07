# Features

from .default import RSEFeatures
from ..lib import arrow_table
from .base import FeatureBase  # NOQA

allowed_features = {
    "rse": {"description": "Features corresponding to RSE jobs", "class": RSEFeatures}
}


def select_features(f):
    "Select featureset"
    if f in allowed_features:
        return allowed_features[f]["class"]
    else:
        return None


def list_features():
    "List available featuresets"
    return arrow_table(
        [(k, allowed_features[k]["description"]) for k in allowed_features],
    )
