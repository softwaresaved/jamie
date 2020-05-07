# Base file for features


import pandas as pd
import numpy as np
from slugify import slugify
from sklearn.model_selection import train_test_split
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.pipeline import Pipeline
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import StandardScaler, LabelBinarizer
from .common.textClean import textClean

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

    def add_textflag(self, text, column):
        col = slugify(text).replace('-', '_')
        cleaner = textClean(remove_stop=False)

        def textflag(text):
            txt = cleaner.clean_text(text)
            for pos, word in enumerate(txt):
                try:
                    if word == 'research' and text[pos + 1] == 'software':
                        return 1
                    elif word == 'research' and txt[pos] == 'software':
                        return 1
                except IndexError:
                    return 0
            return 0

        self.data[col] = self.data[column].apply(textflag)
        return self

    def prepare_labels(self, column):
        y = self.data[(self.data[column] == '0') | (self.data[column] == '1')][column]
        if len(y) == 0:
            y = self.data[(self.data[column] == 0) | (self.data[column] == 1)][column]

        y = y.astype(np.float64)

        lb = LabelBinarizer()
        self.labels = lb.fit_transform(y).ravel()
        return self


def feature_union():
    """
    Pipeline to create a feature union.
    https://medium.com/bigdatarepublic/integrating-pandas-and-scikit-learn-with-pipelines-f70eb6183696
    """
    return FeatureUnion(n_jobs=1, transformer_list=[
                                        ('description', Pipeline([('selector', TextSelector('description')),
                                                        ('tfidf', TfidfVectorizer(sublinear_tf=True, norm='l2', ngram_range=(1, 2), stop_words='english'))
                                        ])),

                                        ('job_title', Pipeline([('selector',
                                                                   TextSelector('job_title')),
                                                        ('tfidf', TfidfVectorizer(sublinear_tf=True, norm='l2', ngram_range=(1, 2), stop_words='english'))
                                        ])),
                                       # ('num_terms_int', Pipeline([('selector', IntSelector('number_terms')),
                                       #                              ('scaler', StandardScaler()),
                                       #  ])),

                                        # ('num_terms_cat', Pipeline([('selector', SoftTermSelector('description')),
                                        # #                             ('encoder', MultiLabelBinarizer(classes=SEARCH_TERM_LIST)),
                                        #                             ('encoder', OneHotEncoder(n_values=len(SEARCH_TERM_LIST)))
                                        # ])),
                                        ('size_txt', Pipeline([('selector', LenSelector('description')),
                                            ('scaler', StandardScaler()),
                                        ])),

                                        # ('research_software', Pipeline([ ('selector', IntSelector('research_software')),
                                        #     # ('labeler', LabelEncoder()),
                                        #     ('encoder', OneHotEncoder())
                                        # ]))
                            # ])),
                        ])
    # X = transformer.fit_transform(df)
    # return X


def get_train_data(prediction_field):

    path_to_df = './data/training_set/training_set.csv'
    df = pd.read_csv(path_to_df)
    # df = find_words(df)
    # df = len_txt(df)
    # clean the text and try to find if there is a research software word in it
    df = check_if_research_software(df, cleaner)

    column_pred_field = '{}_tags'.format(prediction_field)
    # job_ids = df['jobid']
    y = prepare_labels(df, column=column_pred_field)
    features = feature_union()
    X = df[(df[column_pred_field] == '0') | (df[column_pred_field] == '1')][['description', 'job_title', 'research_software']]
    if len(X) == 0:  # Sometimes the labels are integers instead of strings
        X = df[(df[column_pred_field] == 0) | (df[column_pred_field] == 1)][['description', 'job_title', 'research_software']]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    return X_train, X_test, y_train, y_test, features


if __name__ == "__main__":
    get_train_data('aggregate')
