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

def return_collection(self, collection='tags'):
    """
    Return the collection name where the tags are
    """
    return self.db[collection]

def building_pipeline(self, collection, *args, **kwargs):
    """
    Build a pipeline for the aggregator in mongodb.
    1. match: Return the documents that have either SoftwareJob set to Yes or to None in
        the db.tags collection
    2. lookup: do inner join from the jobid keys in the db.collection to find which of the
        jobid are present in the collection given by args[0]
    3. Unwind: the result under the `data` keys to have access to all the keys/values
    4. second_match: only match the results that satisfied the k:v given with **kwargs
    5. project: return only the jobid, the tag and the data

    :params:
        :collection str(): which database need to be queried
        :args: which keys need to be returned. If not args specified, return the entire document
        :kwargs: the keys and values to match which type of data needed to be returned. If none, return all the
        data associated for each keys

    :return: list() pipeline to be parsed into the aggregate function
    """
    match = {'$match': {'$or': [{'SoftwareJob': 'Yes'}, {'SoftwareJob': 'None'}]}}
    lookup = {'$lookup': {'from': collection, 'localField': 'jobid', 'foreignField': 'jobid', 'as': 'data'}}
    unwind = {'$unwind': '$data'}
    field_to_return = {'jobid': 1, 'SoftwareJob': 1, '$data': 1}
    if args:
        added_field_to_return = dict(('data.{}'.format(k), 1) for k in args)
        field_to_return.update(added_field_to_return)

    project = {'$project': field_to_return}
    if kwargs:
        second_match = {'$match': {'$and': [{'data.{}'.format(k): v} for k, v in kwargs.items() if v is not None]}}
        # project = {'$project': {'jobid': 1, 'SoftwareJob': 1, 'data.data': 1}}
        return [match, lookup, unwind, second_match, project]
    return [match, lookup, unwind, project]


def get_documents(self, collection, *args, **kwargs):
    """
    Get a collection object than build the pipeline and return the id, tag and associated vector
    :params:
        :collection: mongDB.collection() collection where txt data are stored
        :args: which keys need to be returned. If not args specified, return the entire document
        :**kwargs: string of the fields that needs to be parsed. The different possibilities are
            :input_field str(): Which field it is from the job advert
            :operation str(): which operation that has been applied on the data to generate it
            :input_data str(): which data have been used. If the collection used is db.txt_clean, this
            field is ommited.
    :return:
        :document[jobid]: str() of the jobid
        :document['SoftwareJob']: str() of the tag associated to the jobid,
            either 'Yes' or 'None'
        :document[0][type_vector]: list() of list() of tuple()
            that contain the vector of the document
    """
    db = self.return_collection()
    pipeline = self.building_pipeline(collection, *args, **kwargs)
    for document in db.aggregate(pipeline):
        try:
            yield document['jobid'], document['SoftwareJob'], document['data']
        except IndexError:  # Happen when the vector is empty because not processed in the vector db
            yield document['jobid'], document['SoftwareJob'], None
        except KeyError:
            raise


def get_training_set(db_conn, collection, *args, **kwargs):
    """
    """
    job_ids = list()
    X = list()
    y = list()
    for job_id, y_, x in db_conn.get_documents(collection, *args, **kwargs):
        job_ids.append(job_id)
        x_unlist = '\n'.join([x[arg] for arg in args])
        X.append(x_unlist)
        y.append(y_)
    return job_ids, X, y

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

    input_field = 'description'
    job_ids, X_train, y_train = get_training_set(db_conn, 'jobs', 'description')
    # tfidf = TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', ngram_range=(1, 2), stop_words='english')
    # features = tfidf.fit_transform(X_train).toarray()
    # print(features.shape)

    # nbr_folds = 20
    #
    # if isinstance(nbr_folds, int):
    #     name_fold = 'kfold-{}'.format(nbr_folds)
    # else:
    #     if nbr_folds.lower() == 'leaveoneout':
    #         nbr_folds = len(y)
    #         name_fold = 'leaveoneout-{}'.format(str(nbr_folds))
    # for collection_data, input_data, input_field, operation in list_of_models:

        # training_set = building_training_set(db_conn, collection_data, input_field, operation, input_data)
        # model_name, model_best_params, model = nested_cross_validation(training_set.X, training_set.y, input_data, input_field, operation, nbr_folds)

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
