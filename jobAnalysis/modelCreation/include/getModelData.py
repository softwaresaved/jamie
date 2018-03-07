#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import os
import re

try:
    from include.getData import collectData
except ModuleNotFoundError:
    from getData import collectData
try:
    from include.logger import logger
except ModuleNotFoundError:
    from logger import logger
try:
    from include.configParser import ConfigParserPerso as configParser
except ModuleNotFoundError:
    from configParser import ConfigParserPerso as configParser

import pymongo

from io import StringIO

import pandas as pd
import numpy as np

logger = logger(name='getModelData', stream_level='DEBUG')


def connectDB():
    """
    """
    CONFIG_FILE = 'config_dev.ini'
    if not os.path.exists(CONFIG_FILE):
        CONFIG_FILE = '../config_dev.ini'
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


def building_pipeline():
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
    lookup = {'$lookup': {'from': 'jobs', 'localField': 'jobid', 'foreignField': 'jobid', 'as': 'data'}}
    # field_to_return = {'jobid': 1, 'SoftwareJob': 1, 'tags': 1, 'data': 1}
    unwind = {'$unwind': '$data'}
    field_to_remove = {'data._id': 0, 'data.jobid': 0, '_id': 0}
    # project = {'$project': field_to_return}
    project2 = {'$project': field_to_remove}
    # return [lookup, unwind, project, project2]
    return [lookup, unwind, project2]


def get_training_set(record=False, path_to_df='../../../outputs/data/model_data.pk1'):
    """
    """
    def collect_data_from_db():
        db = connectDB()
        db_tags = db.return_collection('tags')

        pipeline = building_pipeline()
        for document in db_tags.aggregate(pipeline):
            document.update({k: v for k, v in document['data'].items()})
            del document['data']
            yield document

    df = pd.DataFrame.from_dict(list(collect_data_from_db()))
    if record is True:
        df.to_pickle(path_to_df)

    return df


if __name__ == "__main__":

    get_training_set()
