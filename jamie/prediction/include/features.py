#!/usr/bin/env python
# -*- coding: utf-8 -*-

# __author__: 'Olivier Philippe'


"""
Pipeline to create some features and union them
"""

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

import pickle

import pandas as pd
import numpy as np


from sklearn.model_selection import train_test_split

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer

# from sklearn.pipeline import Pipeline, FeatureUnion
from imblearn.pipeline import Pipeline
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelBinarizer, MultiLabelBinarizer, LabelEncoder


from common.search_term_list import SEARCH_TERM_LIST
from common.textClean import textClean

## Remove some terms from SEARCH_TERM_LIST
## Remove the words modelling/model/modeling from the list as they are too broad terms
to_remove = ['model', 'modelling', 'modeling']
SEARCH_TERM_LIST = [x for x in SEARCH_TERM_LIST if x not in to_remove]

# Transform the list into a dictionary with the word matching a number for the pipeline
# SEARCH_TERM_LIST = {k: i for i, k in enumerate(SEARCH_TERM_LIST)}


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


class SoftTermSelector(IntSelector, textClean):

    def __init__(self, key):
        self.key = key
        textClean.__init__(self)

    def search_term(self, txt):

        def search_per_cell(txt):
            set_of_terms = set()
            clean_txt = self.clean_text(txt)
            for i in SEARCH_TERM_LIST:
                if i in clean_txt:
                    set_of_terms.add(i)
            return list(i for i in set_of_terms)

        return np.array([float(len(search_per_cell(i))) for i in txt]).reshape(-1, 1)

    def transform(self, X):
        return self.search_term(X[self.key])

    def fit(self, X, y=None):
        return self


def find_words(df):

    def return_which_word(row):
        set_to_return = set()
        for i in SEARCH_TERM_LIST:
            if i in row:
                set_to_return.add(i)
        return set_to_return

    ## Create a columns to count the number of time one of the word from the list created in 'search_term.py' appears
    df['search_terms'] = df['description'].apply(lambda x: return_which_word(x))

    ## Create a columns with the number of terms that appears in all the texts
    df['number_terms'] = df['search_terms'].apply(lambda x: len(x))
    # df.number_terms = df.number_terms.astype(str)
    return df


def load_data(path_to_df):

    df = pd.read_csv(path_to_df)
    # try:
    #     df = df.loc[(df.SoftwareJob == 'Yes') | (df.SoftwareJob == 'None')]
    # except TypeError:
    #     pass
    return df


def check_if_research_software(df, cleaner):
    """
    Parse the description and check if there is a presence of research software in the text
    """

    def check_if_rs(cleaner, txt):
        txt = cleaner.clean_text(txt)
        for pos, word in enumerate(txt):
            try:
                if word == 'research' and txt[pos+1] == 'software':
                    return 1
                elif word == 'research' and txt[pos] == 'software':
                    return 1
            except IndexError:
                return 0
        return 0

    df['research_software'] = df['description'].apply(lambda x: check_if_rs(cleaner, x))
    return df


def prepare_labels(df, column, binary):

    if binary == True:
        y = df[(df[column] == '0') | (df[column] == '1')][column]
        if len(y) == 0:
            y = df[(df[column] == 0) | (df[column] == 1)][column]

        y = y.astype(np.float64)
    else:
        y = df[column]

    if len(set(y)) > 2:
        lb = MultiLabelBinarizer()
        # raise('Not implemented yet')
    else:
        # Relabel the 'yes' to 1 and 'no' to 0
        lb = LabelBinarizer()
    y_train = lb.fit_transform(y)
    # Need to apply the ravel otherwise it is not the right shape
    print(y)
    y = lb.fit_transform(y).ravel()
    print(y)
    return y


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


def get_train_data(prediction_field, binary=True):

    path_to_df = './data/training_set/training_set.csv'
    df = load_data(path_to_df)
    # df = find_words(df)
    # df = len_txt(df)
    # clean the text and try to find if there is a research software word in it
    cleaner = textClean(remove_stop=False)
    df = check_if_research_software(df, cleaner)

    column_pred_field = '{}_tags'.format(prediction_field)
    # job_ids = df['jobid']
    y = prepare_labels(df, column=column_pred_field, binary=binary)
    features = feature_union()
    if binary == True:
        X = df[(df[column_pred_field] == '0') | (df[column_pred_field] == '1')][['description', 'job_title', 'research_software']]
        if len(X) == 0:

            X = df[(df[column_pred_field] == 0) | (df[column_pred_field] == 1)][['description', 'job_title', 'research_software']]

    else:
        X = df[['description', 'job_title', 'research_software']]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    return X_train, X_test, y_train, y_test, features


if __name__ == "__main__":
    get_train_data('aggregate')