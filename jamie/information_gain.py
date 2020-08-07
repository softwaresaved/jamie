import operator
import numpy as np
from scipy.stats import rankdata
from sklearn.feature_extraction.text import CountVectorizer
from collections import defaultdict
import pandas as pd
from .snapshots import TrainingSnapshot
from .text_clean import TextClean


def L(col, y):  # as in (2.5) on p29 of Fundamentals of Predictive Text Mining
    N = len(col)
    assert len(y) == N
    _JF = defaultdict(int)
    for i in range(N):
        _JF[col[i], y[i]] += 1
    JF = np.array([_JF[0, 0], _JF[0, 1], _JF[1, 0], _JF[1, 1]]).reshape(
        2, 2
    )  # joint frequencies
    F = np.array([len(col[col == k]) for k in [0, 1]])
    P = (F + 1) / (N + 2)
    JP = (JF + 1) / (np.array((F + 2), ndmin=2).T)
    E = JP * np.log2(1 / JP)
    return np.dot(P, E.sum(axis=1))


def V(col, y):  # as in (2.5) on p29 of Fundamentals of Predictive Text Mining
    N = len(col)
    assert len(y) == N
    _JF = defaultdict(int)
    for i in range(N):
        _JF[col[i], y[i]] += 1
    F = np.array([len(col[col == k]) for k in [0, 1]])
    return F[0], F[1], _JF[0, 0], _JF[0, 1], _JF[1, 0], _JF[1, 1]


class InformationGainTransformer:
    def __init__(self, rank_method="dense"):
        self.rank_method = rank_method
        self._information_gain = None
        self._ranked = None

    def fit(self, X, y, names):
        self.names = names
        T = X.copy()  # make a copy
        T[T != 0] = 1  # binarize it
        if T.shape[1] != len(names):
            raise ValueError(
                "Incompatible shapes: X %s names %d" % (repr(X.shape), len(names))
            )
        if T.shape[0] != len(y):
            raise ValueError(
                "Incompatible shapes: X %s y %r" % (repr(X.shape), y.shape)
            )
        self._information_gain = np.array(
            [L(T[:, k].toarray().squeeze(), y) for k in range(T.shape[1])]
        )
        self._ranked = rankdata(self._information_gain, method=self.rank_method)

    def fit_transform(self, X, y, names):
        self.fit(X, y, names)
        return self._information_gain

    def sorted_dataframe(self):
        if self._information_gain is None:
            raise ValueError(
                "InformationGainTransformer().fit needs to be "
                "called before sorted_dataframe()"
            )
        return pd.DataFrame(
            data=sorted(
                list(zip(self._information_gain, self.names)),
                key=operator.itemgetter(0),
            ),
            columns=["information", "ngram"],
        )

    def indices_till_rank(self, rank):
        if self._ranked is None:
            raise ValueError(
                "InformationGainTransformer().fit needs to be"
                "called before indices_till_rank()"
            )
        if rank == 0:
            raise ValueError("Rank should be positive or negative but not zero.")
        if rank > 0:
            return np.array(
                [idx for idx, r in list(enumerate(self._ranked)) if r <= rank]
            )
        else:
            max_rank = max(self._ranked)
            return np.array(
                [
                    idx
                    for idx, r in list(enumerate(self._ranked))
                    if r >= (max_rank + rank + 1)
                ]
            )

    def indices_at_rank(self, rank):
        if self._ranked is None:
            raise ValueError(
                "InformationGainTransformer().fit needs to be "
                "called before indices_at_rank()"
            )
        return np.array([idx for idx, r in list(enumerate(self._ranked)) if r == rank])


def _information_gain(training_snapshot, text_column, output_column="aggregate_tags"):
    ts = TrainingSnapshot(training_snapshot)
    data = ts.data
    cleaner = TextClean()
    data[text_column] = data[text_column].apply(
        lambda x: " ".join(cleaner.clean_text(x))
    )
    vec = CountVectorizer(ngram_range=(1, 2), stop_words="english")
    X = vec.fit_transform(data[text_column])
    ig = InformationGainTransformer()
    ig.fit(X, data[output_column], vec.get_feature_names())
    fn = ts.path / "informationgain_{}__{}.csv".format(text_column, output_column)
    ig.sorted_dataframe().to_csv(fn, index=False)
    return fn
