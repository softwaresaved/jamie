#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from io import StringIO

import pymongo
import pandas as pd
import numpy as np


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import preprocessing
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import KFold, cross_val_score, GridSearchCV, LeaveOneOut, StratifiedKFold, RandomizedSearchCV
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
import sklearn.exceptions

import warnings
warnings.filterwarnings('ignore', category=sklearn.exceptions.UndefinedMetricWarning)


from common.logger import logger
from common.getConnection import connectDB

logger = logger(name='prediction', stream_level='DEBUG')

# ## GLOBAL VARIABLES  ###
# # To set up the variable on prod or dev for config file and level of debugging in the
# # stream_level
RUNNING = 'dev'

if RUNNING == 'dev':
    CONFIG_FILE = '../config/config_dev.ini'
    DEBUGGING='DEBUG'
elif RUNNING == 'prod':
    CONFIG_FILE = '../config/config.ini'
    DEBUGGING='INFO'


def nested_cross_validation(X, y, feature, nbr_folds=2):
    """
    Dev version of the training instance
    Source: https://datascience.stackexchange.com/a/16856
    """
    print(set(y))
    raise
    if len(set(y)) > 2:
        # Relabel the 'yes' to 1 and 'no' to 0
        lb = preprocessing.LabelBinarizer()
    y = lb.fit_transform(y)
    print(y)
    # Reshaped the matrix for working with StratifiedKFold
    # see: https://stackoverflow.com/a/35022548/3193951
    # y = np.reshape(y, [len(y)])

    # prepare models
    models = []
    # models.append(('LR', LogisticRegression()))
    # models.append(('LDA', LinearDiscriminantAnalysis()))
    # models.append(('KNN', KNeighborsClassifier()))
    # models.append(('CART', DecisionTreeClassifier()))
    # models.append(('NB', GaussianNB()))
    c_params = 10. ** np.arange(-3, 8)
    gamma_params = 10. ** np.arange(-5, 4)

    models = {'SVC': {'model': SVC(),
                      'param_grid': [{'C': c_params,
                                      'gamma': gamma_params,
                                      'kernel': ['rbf']},
                                      # 'class_weight': ['balanced', None]},
                                     {'C': c_params,
                                      'kernel': ['linear']}]
                      },
              'CART': {'model': DecisionTreeClassifier(),
                       'param_grid': [{'max_depth': range(3, 20)}]
                      }
              }

    # Create the outer_cv with 3 folds for estimating generalization error
    # outer_cv = StratifiedKFold(nbr_folds)
    # outer_csv = LeaveOneOut()
    # outer_cv  = LeaveOneOut(nbr_folds)
    outer_cv = KFold(nbr_folds)

    # When trained a certain fold, doing the second cross-validation split to choose hyper parameters
    if isinstance(nbr_folds, int):
        inner_cv = StratifiedKFold(nbr_folds)
        outer_cv = StratifiedKFold(nbr_folds)
        name_outer_cv = 'kfold-{}'.format(nbr_folds)
    else:
        if nbr_folds.lower() == 'leaveoneout':
            inner_cv = LeaveOneOut()
            outer_cv = LeaveOneOut()
            nbr_folds = len(y)
            name_outer_cv = 'leaveoneout-{}'.format(str(nbr_folds))

    score_for_outer_cv = pd.DataFrame(index=range(len(models)),
                                      columns=['model', 'feature'])
    score_for_outer_cv['model'] = [name for name in models]

    columns_to_add = ['fold-{}'.format(int(i)+ 1) for i in range(nbr_folds)]
    score_for_outer_cv = score_for_outer_cv.reindex(columns=score_for_outer_cv.columns.tolist() + columns_to_add)

    average_scores_across_outer_folds_for_each_model = dict()
    # Get the average of the scores for the 10 folds
    for i, name in enumerate(models):

        model_opti_hyper_params = GridSearchCV(estimator=models[name]['model'],
                                               param_grid=models[name]['param_grid'],
                                               cv=inner_cv,
                                               scoring='f1',
                                               n_jobs=-1)

        # estimate generalization error on the K-fold splits of the data
        scores_across_outer_folds = cross_val_score(model_opti_hyper_params,
                                                    X, y,
                                                    cv=outer_cv,
                                                    scoring='f1',
                                                    n_jobs=-1)

        score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['feature']] = feature
        score_for_outer_cv.iloc[i, -nbr_folds:] = scores_across_outer_folds

        # get the mean MSE across each of outer_cv's K-folds
        average_scores_across_outer_folds_for_each_model[name] = np.mean(scores_across_outer_folds.mean())
        error_summary = 'Model: {name}\nMSE in the {nbr_folds} outer folds: {scores}.\nAverage error: {avg}'
        print(error_summary.format(name=name, nbr_folds=nbr_folds,
                                   scores=scores_across_outer_folds,
                                   avg=np.mean(scores_across_outer_folds)))
        print()



    record_result_csv(score_for_outer_cv, name_outer_cv)
    print('Average score across the outer folds: ', average_scores_across_outer_folds_for_each_model)
    many_stars = '\n' + '*' * 100 + '\n'
    print(many_stars + 'Fitting the model on the training set Complete summary of the best model' + many_stars)

    best_model_name, best_model_avg_score = max(average_scores_across_outer_folds_for_each_model.items(),
                                                key=(lambda name_averagescore: name_averagescore[1]))

    # get the best model and its associated parameter grid
    best_model, best_model_params = models[best_model_name]['model'], models[best_model_name]['param_grid']

    # now we refit this best model on the whole dataset so that we can start
    # making predictions on other data, and now we have a reliable estimate of
    # this model's generalization error and we are confident this is the best model
    # among the ones we have tried
    final_model = GridSearchCV(best_model, best_model_params, cv=inner_cv, n_jobs=-1)
    final_model.fit(X, y)
    best_params = final_model.best_params_
    print(best_params)

    # return best_model, best_model_params
    return best_model_name, best_params, final_model


if __name__ == "__main__":

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)
    db_dataset = db_conn['jobs']
    path_to_df = './data/model_data.pk1'
    df = pd.read_pickle(path_to_df)
    train_df = df[df.SoftwareJob.notnull()]
    job_ids, X_train, y_train = train_df['jobid'], train_df['description'], train_df['SoftwareJob']
    # print(X_train)
    tfidf = TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', ngram_range=(1, 2), stop_words='english')
    features = tfidf.fit_transform(X_train).toarray()
    print(features.shape)

    model_name, model_best_params, model = nested_cross_validation(features, y_train, 'description', nbr_folds=2)

        # vectorising_data = vectorProcess(dict_name='_'.join([collection_data, input_field, input_data, operation, 'vector']))
        # m=0
        # n=0
        # nbr_yes = 0
        # nbr_no = 0
        # db_doc = db_conn.return_collection(collection=collection_data)
        # for document in db_doc.find({'input_field': input_field,
        #                              'operation': operation,
        #                              'input_data': input_data,
        #                              'data': {'$exists': True}}):
        #     m+=1
        #     try:
        #         data_vector = vectorising_datr.get_vector(document['data'], update_dict=False)
        #         data_sparse_matrix = training_set.create_sparse_matrix(data_vector, training_set.max_vector)
        #         data_tfidf = training_set.transform_tfidf(data_sparse_matrix)
        #
        #
        #         prediction = model.predict(data_tfidf)[0]
        #         # prediction = model.predict(data_sparse_matrix)[0]
        #         if prediction == 0:
        #             prediction = 'No'
        #         if prediction == 1:
        #             prediction = 'Yes'
        #         db_prediction.update({'jobid': document['JobId'],
        #                                 'input_field': input_field,
        #                                 'input_data': input_data,
        #                                 'operation': operation,
        #                                 'model': model_name,
        #                                 'folding': name_fold,
        #                                 'params': model_best_params},
        #                                 {'$set': {'prediction': prediction}},
        #                                 upsert=True)
        #         n+=1
        #         if prediction == 'Yes':
        #             nbr_yes +=1
        #         if prediction == 'No':
        #             nbr_no +=1
        #
        #         if m % 5000 == 0:
        #             print('Number of document processed: {}'.format(m))
        #             print('Number of document classified: {}'.format(n))
        #             print('Number of Yes: {}'.format(nbr_yes))
        #             print('Number of No: {}'.format(nbr_no))
        #             print('\n')
        #     except KeyError:
        #         pass
        #     except ValueError:
        #         pass
