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

from sklearn.model_selection import KFold, cross_val_score, GridSearchCV, LeaveOneOut, StratifiedKFold, RandomizedSearchCV
from sklearn import preprocessing
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
# from sklearn.model_selection import train_test_split
import sklearn.exceptions

import warnings
warnings.filterwarnings('ignore', category=sklearn.exceptions.UndefinedMetricWarning)


from common.logger import logger
from common.configParser import ConfigParserPerso as configParser

logger = logger(name='prediction', stream_level='DEBUG')


def connectDB():
    """
    """
    CONFIG_FILE = 'config_dev.ini'
    config_value = configParser()
    config_value.read(CONFIG_FILE)

    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)
    access_value = configParser()
    access_value.read(DB_ACC_FILE)

    # # MongoDB ACCESS # #
    mongoDB_USER = access_value['MongoDB'].get('db_username'.lower(), None)
    mongoDB_PASS = access_value['MongoDB'].get('DB_PASSWORD'.lower(), None)
    mongoDB_AUTH_DB = access_value['MongoDB'].get('DB_AUTH_DB'.lower(), None)
    mongoDB_AUTH_METH = access_value['MongoDB'].get('DB_AUTH_METHOD'.lower(), None)

    # Get the information about the db and the collections
    mongoDB_NAME = config_value['MongoDB'].get('DB_NAME'.lower(), None)

    # Create the instance that connect to the db storing the training set
    mongoDB = collectData(mongoDB_NAME, mongoDB_USER,
                          mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    return mongoDB


def building_training_set(db_conn, collection_data, input_field, operation, input_data=None, tfidf=True):
    """
    """
    record_result_name = '_'.join([x for x in [collection_data, input_field, input_data, operation] if x])
    db_training_set = db_conn.get_documents(collection_data, operation=operation,
                                            input_data=input_data,
                                            input_field=input_field)

    vector_dic = '{}_vector'.format(record_result_name)
    training_data = trainingData(db_training_set, dict_name=vector_dic)
    training_data.run(tfidf)
    training_data.save_dict()
    return training_data


def record_result_csv(df, name_folds):
    """
    Record the result of each outer_cv loop into a panda df and
    then record it into a csv.
    Before saving it checks if a similar csv file exists to append it instead
    of overwritting it.
    The name is based on the method to folds and just write the different models unders
    """
    filename = './../report/results/prediction/average_scores_' + name_folds+ '.csv'
    if os.path.isfile(filename):
        df_to_append = pd.read_csv(filename, index_col=0)
        df_to_append = df_to_append.append(df)
        df_to_append.to_csv(filename)
    else:
        df.to_csv(filename)


def report_to_df(report):
    """
    Source: https://stackoverflow.com/a/46447871/3193951
    """
    report = re.sub(r" +", " ", report).replace("avg / total", "avg/total").replace("\n ", "\n")
    report_df = pd.read_csv(StringIO("Classes" + report), sep=' ', index_col=0)
    return report_df


def nested_cross_validation(X, y, input_data, input_field, operation, nbr_folds=2):
    """
    Dev version of the training instance
    Source: https://datascience.stackexchange.com/a/16856
    """
    # Relabel the 'yes' to 1 and 'no' to 0
    lb = preprocessing.LabelBinarizer()
    y = lb.fit_transform(y)
    # Reshaped the matrix for working with StratifiedKFold
    # see: https://stackoverflow.com/a/35022548/3193951
    y = np.reshape(y, [len(y)])

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
                                      columns=['model', 'input_data', 'input_field', 'operation'])
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

        score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['input_data']] = input_data
        score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['input_field']] = input_field
        score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['operation']] = operation
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
    db_conn = connectDB()
    db_dataset = db_conn.return_collection(collection='jobs')
    db_prediction = db_conn.return_collection(collection='prediction')
    db_prediction.create_index([('jobid', pymongo.DESCENDING),
                                ('input_field', pymongo.ASCENDING),
                                ('operation', pymongo.ASCENDING),
                                ('input_data', pymongo.ASCENDING),
                                ('model', pymongo.ASCENDING),
                                ('folding', pymongo.ASCENDING),
                                ('params', pymongo.ASCENDING)],
                               unique=True)
    # list of tuples that has all the models
    list_of_models = list()

    ### DESCRIPTION
    # lemmatise - Description
    collection_data = 'txt_feature'
    input_data = 'clean'
    input_field = 'Description'
    operation = 'lemmatise'
    list_of_models.append((collection_data, input_data, input_field, operation))

    # # 2gram on Description clean word
    collection_data = 'txt_feature'
    input_data = 'clean_wo_stop'
    input_field = 'Description'
    operation = '2gram'
    list_of_models.append((collection_data, input_data, input_field, operation))


    ###  JOB TITLE
    # # lemmatise  JobTitle
    collection_data = 'txt_feature'
    input_data = 'clean'
    input_field = 'JobTitle'
    operation = 'lemmatise'
    list_of_models.append((collection_data, input_data, input_field, operation))

    # # 2gram on title clean word
    collection_data = 'txt_feature'
    input_data = 'clean_wo_stop'
    input_field = 'JobTitle'
    operation = '2gram'
    list_of_models.append((collection_data, input_data, input_field, operation))

    nbr_folds = 20

    if isinstance(nbr_folds, int):
        name_fold = 'kfold-{}'.format(nbr_folds)
    else:
        if nbr_folds.lower() == 'leaveoneout':
            nbr_folds = len(y)
            name_fold = 'leaveoneout-{}'.format(str(nbr_folds))

    for collection_data, input_data, input_field, operation in list_of_models:

        training_set = building_training_set(db_conn, collection_data, input_field, operation, input_data)
        model_name, model_best_params, model = nested_cross_validation(training_set.X, training_set.y, input_data, input_field, operation, nbr_folds)

        vectorising_data = vectorProcess(dict_name='_'.join([collection_data, input_field, input_data, operation, 'vector']))
        m=0
        n=0
        nbr_yes = 0
        nbr_no = 0
        db_doc = db_conn.return_collection(collection=collection_data)
        for document in db_doc.find({'input_field': input_field,
                                     'operation': operation,
                                     'input_data': input_data,
                                     'data': {'$exists': True}}):
            m+=1
            try:
                data_vector = vectorising_data.get_vector(document['data'], update_dict=False)
                data_sparse_matrix = training_set.create_sparse_matrix(data_vector, training_set.max_vector)
                data_tfidf = training_set.transform_tfidf(data_sparse_matrix)


                prediction = model.predict(data_tfidf)[0]
                # prediction = model.predict(data_sparse_matrix)[0]
                if prediction == 0:
                    prediction = 'No'
                if prediction == 1:
                    prediction = 'Yes'
                db_prediction.update({'jobid': document['JobId'],
                                        'input_field': input_field,
                                        'input_data': input_data,
                                        'operation': operation,
                                        'model': model_name,
                                        'folding': name_fold,
                                        'params': model_best_params},
                                        {'$set': {'prediction': prediction}},
                                        upsert=True)
                n+=1
                if prediction == 'Yes':
                    nbr_yes +=1
                if prediction == 'No':
                    nbr_no +=1

                if m % 5000 == 0:
                    print('Number of document processed: {}'.format(m))
                    print('Number of document classified: {}'.format(n))
                    print('Number of Yes: {}'.format(nbr_yes))
                    print('Number of No: {}'.format(nbr_no))
                    print('\n')
            except KeyError:
                pass
            except ValueError:
                pass
