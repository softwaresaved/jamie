# Features

from .default import RSEFeatures
from ..lib import arrow_table
from .base import FeatureBase  # NOQA

featuresets = {"rse": RSEFeatures}


def select_features(f):
    "Select featureset from name"
    return featuresets.get(f, None)


def list_features():
    "List available featuresets"
    return arrow_table([(f, featuresets[f].description) for f in featuresets])


def valid_doc(features, doc):
    """Check whether document is valid according to featureset required
    columns. Each featureset usually requires some attributes to be present
    in the data for a valid feature transformation.

    Returns
    -------
    bool
        Whether document is valid
    """
    return doc is not None and all(
        doc[x][0] is not None for x in featuresets[features].require_columns
    )
