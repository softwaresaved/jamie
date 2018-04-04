#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Script to connect to the MongoDB and collect the training set from the collection called
tags, containing the classified jobs, and the collection called 'jobs' where all the features
are stored.
It return a dataframe and store it in a pickle form for later use
"""


import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from io import StringIO

import pymongo
import pandas as pd
import numpy as np

from common.logger import logger
from common.getConnection import connectDB

logger = logger(name='getTrainingSet', stream_level='DEBUG')

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


def building_pipeline(collection, *args, **kwargs):
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
    lookup = {'$lookup': {'from': collection, 'localField': 'jobid', 'foreignField': 'jobid', 'as': 'data'}}
    unwind = {'$unwind': '$data'}

    field_to_return = {'jobid': 1, 'SoftwareJob': 1, 'tags': 1, 'data': 1}

    if args:
        added_field_to_return = dict(('data.{}'.format(k), 1) for k in args)
        field_to_return.update(added_field_to_return)
        del field_to_return['data']

    project = {'$project': field_to_return}

    field_to_remove = {'_id': 0, 'data._id': 0, 'data.jobid': 0}
    project2 = {'$project': field_to_remove}

    if kwargs:
        second_match = {'$match': {'$and': [{'data.{}'.format(k): v} for k, v in kwargs.items() if v is not None]}}
        return [lookup, unwind, second_match, project, project2]
    return [lookup, unwind, project, project2]


def get_documents(db, collection, *args, **kwargs):
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
    pipeline = building_pipeline(collection, *args, **kwargs)
    for document in db['tags'].aggregate(pipeline):
        # yield document
        try:
            del document['data']['_id']
        except KeyError:
            pass
        try:
            del document['_id']
        except KeyError:
            document.update(document['data'])
        try:
            del document['data']
        except KeyError:
            pass
        yield document


def get_training_set(db, collection, *args, record=False, **kwargs):
    """
    """
    df = pd.DataFrame.from_dict(list(get_documents(db, collection, *args, **kwargs)))
    if record is True:
        path_to_df = './data/model_data.pk1'
        df.to_pickle(path_to_df)
    return df


if __name__ == "__main__":

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)
    df = get_training_set(db_conn, 'jobs', record=True)
    print(df)


