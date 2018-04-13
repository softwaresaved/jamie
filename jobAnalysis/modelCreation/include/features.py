#!/usr/bin/env python
# -*- coding: utf-8 -*-


import pandas as pd
import numpy as np


from sklearn.model_selection import train_test_split

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelBinarizer, MultiLabelBinarizer, LabelEncoder


from common.search_term_list import SEARCH_TERM_LIST
from common.textClean import textClean


class TextSelector(BaseEstimator, TransformerMixin):

    def __init__(self, key):
        self.key = key

    def fit(self, x, y=None):
        return self

    def transform(self, data_dict):
        return data_dict[self.key]

class IntSelector(TextSelector):

    def transform(self, data_dict):
        return data_dict[[self.key]]


def load_data(path_to_df):

    df = pd.read_pickle(path_to_df)
    df = df.loc[(df.SoftwareJob == 'Yes') | (df.SoftwareJob == 'None')]
    return df


def len_txt(df):
    """
    Size of the description
    """
    df['size_description'] = df['description'].apply(lambda x: len(x))
    return df


def find_words(df):

    def return_which_word(row):
        set_to_return = set()
        for i in modified_term_list:
            if i in row:
                set_to_return.add(i)
        return set_to_return

    ## Remove the words modelling/model/modeling from the list as they are too broad terms
    to_remove = ['model', 'modelling', 'modeling']
    modified_term_list = [x for x in SEARCH_TERM_LIST if x not in to_remove]


    ## Create a columns to count the number of time one of the word from the list created in 'search_term.py' appears
    df['search_terms'] = df['description'].apply(lambda x: return_which_word(x))

    ## Create a columns with the number of terms that appears in all the texts
    df['number_terms'] = df['search_terms'].apply(lambda x: len(x))
    # df.number_terms = df.number_terms.astype(str)
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
            except IndexError:
                return 0
        return 0

    df['research software'] = df['description'].apply(lambda x: check_if_rs(cleaner, x))
    return df


def prepare_labels(df):

    y = df['SoftwareJob']
    if len(set(y)) > 2:
        lb = MultiLabelBinarizer()
        # raise('Not implemented yet')
    else:
        # Relabel the 'yes' to 1 and 'no' to 0
        lb = LabelBinarizer()
        y_train = lb.fit_transform(y)
        # Need to apply the ravel otherwise it is not the right shape
        y = lb.fit_transform(y).ravel()
    return y


def prepare_features(df):
    """
    Pipeline to create a feature union.
    https://medium.com/bigdatarepublic/integrating-pandas-and-scikit-learn-with-pipelines-f70eb6183696
    """
    transformer = Pipeline([('features', FeatureUnion(n_jobs=1,
                                                      transformer_list=[
                                        ('description', Pipeline([('selector', TextSelector('description')),
                                                        ('tfidf', TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', ngram_range=(1, 2), stop_words='english'))
                                        ])),

                                        ('job_title', Pipeline([('selector',
                                                                   TextSelector('job_title')),
                                                        ('tfidf', TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', ngram_range=(1, 2), stop_words='english'))
                                        ])),
                                       ('num_terms_int', Pipeline([('selector', IntSelector('number_terms')),
                                                                    ('scaler', StandardScaler()),
                                        ])),

                                        ('num_terms_cat', Pipeline([('selector',
                                                                    IntSelector('number_terms')),
                                            # ('labeler', LabelEncoder()),
                                                                    ('encoder', OneHotEncoder())
                                        ])),
                                        ('size_txt', Pipeline([('selector', IntSelector('size_description')),
                                            ('scaler', StandardScaler()),
                                        ])),

                                        ('research_software', Pipeline([ ('selector', IntSelector('number_terms')),
                                            # ('labeler', LabelEncoder()),
                                            ('encoder', OneHotEncoder())
                                        ]))
                            ])),
                        ])
    X = transformer.fit_transform(df)
    return X


def get_train_data():

    path_to_df = './data/model_data.pk1'
    df = load_data(path_to_df)
    df = find_words(df)
    df = len_txt(df)
    # clean the text and try to find if there is a research software word in it
    cleaner = textClean(remove_stop=False)
    df = check_if_research_software(df, cleaner)

    # job_ids = df['jobid']
    y = prepare_labels(df)
    X = prepare_features(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    return X_train, X_test, y_train, y_test

