# Base file for features


import pandas as pd
import numpy as np
from slugify import slugify
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import LabelBinarizer
from ..common.textClean import textClean

class TextSelector(BaseEstimator, TransformerMixin):

    def __init__(self, key):
        self.key = key

    def transform(self, X):
        return X[self.key]

    def fit(self, X, y=None):
        return self


class IntSelector(TextSelector):

    def transform(self, X):
        return X[[self.key]]


class LenSelector(IntSelector):

    def len_txt(self, txt):
        return np.array([float(len(t)) for t in txt]).reshape(-1, 1)

    def transform(self, X):
        return self.len_txt(X[self.key])


class FeatureBase:
    """Base feature class"""

    def __init__(self, data, search_term_list, require_columns):
        self.search_term_list = search_term_list
        self.data = pd.read_csv(data)
        if any(f not in self.data for f in require_columns):
            raise ValueError("Missing one of required columns %r" % require_columns)

    def find_searchterms(self, row):
        return set(i for i in self.search_term_list if i in row)

    def combine_features(self, features):
        self.features = FeatureUnion(n_jobs=1, transformer_list=features)
        return self

    def add_searchterm(self, column):
        self.data['searchterm_%s' % column] = self.data[column].apply(self.find_searchterms)
        return self

    def add_countterm(self, column):
        if 'searchterm_%s' % column not in self.data:  # add searchterm field if not exists
            self.add_searchterm(column)
        self.data['nterm_%s' % column] = self.data['searchterm_%s' % column].apply(len)
        return self

    def add_textflag(self, search_for, in_column):
        col = slugify(search_for).replace('-', '_')
        cleaner = textClean(remove_stop=False)
        self.data[col] = self.data[in_column].apply(
            lambda x: search_for in ' '.join(cleaner.clean_text(x)))
        return self

    def prepare_labels(self, column):
        y = self.data[(self.data[column] == '0') | (self.data[column] == '1')][column]
        if len(y) == 0:
            y = self.data[(self.data[column] == 0) | (self.data[column] == 1)][column]

        y = y.astype(np.float64)

        lb = LabelBinarizer()
        self.labels = lb.fit_transform(y).ravel()
        return self

    def make_arrays(self, prediction_field):
        pass
