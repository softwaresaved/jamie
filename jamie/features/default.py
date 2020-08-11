# Default features for RSE jobs
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.pipeline import Pipeline
from .base import FeatureBase, TextSelector


def _tfidf(max_features=None, pipeline_name="tfidf"):
    "Tfidf wrapper for pipeline with default arguments"
    return (
        pipeline_name,
        TfidfVectorizer(
            sublinear_tf=True,
            norm="l2",
            max_features=max_features,
            ngram_range=(1, 2),
            stop_words="english",
        ),
    )


def _text_feature(name, max_features=None, column=None):
    """Returns text feature pipeline component. If column is not specified,
    defaults to the name parameter"""
    return (
        name,
        Pipeline([("selector", TextSelector(column or name)), _tfidf(max_features)]),
    )


class RSEFeatures(FeatureBase):
    """Default featureset for finding Research Software Engineering (RSE) jobs.
    To see the methods, see :class:`FeatureBase`.
    The featureset encodes the following features:

    * *description*: Description text of job, transformed as below
    * *job_title*: Job title, transformed as below

    The text is transformed using TF-IDF to produce unigrams and bigrams
    after removing stopwords, and using sublinear TF scaling.
    """

    require_columns = ["description", "job_title"]
    description = "Features corresponding to RSE jobs"

    def __init__(self, data):
        super().__init__(
            data,
            require_columns=self.require_columns,
            clean_columns=self.require_columns,
        )
        self.set_features(
            [_text_feature("description", 24000), _text_feature("job_title")]
        )

    def make_arrays(self, prediction_field):
        self._prepare_labels(prediction_field)
        print("Positive Labels:", self.labels.sum())
        self.data[prediction_field] = self.data[prediction_field].astype(str)
        self.X = self.data[
            (self.data[prediction_field] == "0") | (self.data[prediction_field] == "1")
        ][["description", "job_title"]]
        return self


if __name__ == "__main__":
    data = (
        Path(__file__).parent.parent
        / "prediction"
        / "data"
        / "training_set"
        / "training_set.csv"
    )
    fs = RSEFeatures(data).make_arrays("aggregate_tags")
