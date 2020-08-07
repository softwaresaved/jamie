# Default features for RSE jobs
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.pipeline import Pipeline
from .base import FeatureBase, TextSelector
from sklearn.preprocessing import StandardScaler
from .base import CountTerm, LenSelector

SEARCH_TERM_LIST = [
    "algorithm",
    "big data",
    "beautifulsoup",
    "code",
    "computation",
    "computational",
    "computed",
    "computer",
    "data analysis",
    "data base",
    "database",
    "excel",
    "fortran",
    "geographic information science",
    "geographic information systems",
    "gis",
    "git",
    "github",
    "graphics",
    "high performance computing",
    "hpc",
    "imagej",
    "implemented in",
    "in silico",
    "matlab",
    "matplotlib",
    "numpy",
    "nvivo",
    "open source",
    "open-source",
    "pipeline",
    "python",
    "quantitative",
    "regression",
    "r language",
    "in r",
    "scrapy",
    "scipy",
    "simulated",
    "simulation",
    "software",
    "spss",
    "sqlalchemy",
    "stata",
    "statistical" "supercomputing",
    "visualisation",
    "visualization",
    "Rcpp",
    "ggplot2",
    "plyr",
    "stringr",
    "reshape2",
    "RColorBrewer",
    "workflow",
    "wxpython",
]


class RSEFeatures(FeatureBase):
    """Default featureset for finding Research Software Engineering (RSE) jobs.
    To see the methods, see :class:`FeatureBase`.
    The featureset encodes the following features:

    * *description*: Description text of job, transformed as below
    * *job_title*: Job title, transformed as below

    The text is transformed using TF-IDF to produce unigrams and bigrams
    after removing stopwords, and using sublinear TF scaling.
    """

    def __init__(self, data):
        super().__init__(
            data,
            SEARCH_TERM_LIST,
            require_columns=["description", "job_title"],
            clean_columns=["description", "job_title"],
        )
        self.set_features(
            [
                (
                    "description",
                    Pipeline(
                        [
                            ("selector", TextSelector("description")),
                            (
                                "tfidf",
                                TfidfVectorizer(
                                    sublinear_tf=True,
                                    norm="l2",
                                    max_features=24000,
                                    ngram_range=(1, 2),
                                    stop_words="english",
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    "job_title",
                    Pipeline(
                        [
                            ("selector", TextSelector("job_title")),
                            (
                                "tfidf",
                                TfidfVectorizer(
                                    sublinear_tf=True,
                                    norm="l2",
                                    ngram_range=(1, 2),
                                    stop_words="english",
                                ),
                            ),
                        ]
                    ),
                ),
                # ('count_term', Pipeline([('selector', TextSelector('description')),
                #                          ('count', CountTerm(self.search_term_list)),
                #                          ('scale', StandardScaler())])),
                # ('len_txt', Pipeline([('length', LenSelector('description')),
                #                       ('scale', StandardScaler())]))
            ]
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
