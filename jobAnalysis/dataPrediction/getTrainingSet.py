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
from common.getArgs import getArgs
from common.getConnection import connectMongo

logger = logger(name='getTrainingSet', stream_level='DEBUG')


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

    field_to_return = {'jobid': 1, 'run_tag': 1, 'tags': 1, 'data': 1}

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
        :document[0][type_vector]: list() of list() of tuple()
            that contain the vector of the document
    """
    pipeline = building_pipeline(collection, *args, **kwargs)
    for document in db['tags'].aggregate(pipeline):
        document.update({k: v for k, v in document['data'].items()})
        document['tags'] = [x if x != 'None' else 'No' for x in document['tags']]
        try:
            del document['data']
        except KeyError:
            pass
        yield document


def get_training_set(db, collection, *args, **kwargs):
    """
    """
    df = pd.DataFrame.from_dict(list(get_documents(db, collection, *args, **kwargs)))
    return df


def previous_tags(row):
    insuff = 0
    no = 0
    some = 0
    most = 0
    if row[-1] != 'third_run':
        for r in row[:-1]:
            if r == 'No':
                no +=1
            elif r == 'Some':
                some +=1
            elif r == 'Most':
                most +=1
            elif r == 'Insufficient Evidence':
                insuff +=1
            else:
                pass
        if most >= 2:
            return 1
        elif some >=2:
            return 1
        elif no >=2:
            return 0
        elif insuff >=2:
            return 'Insufficient Evidence'
        else:
            return 'Ambiguous'
    else:
        return 'third_run'


def calculate_score(row):
    """
    This function aggregate the different tags given by people to a job ads into an integrate one, computed with the
    mean and some other calculation to reflect the different possibilities given.
    The different possibilities were:
        1. Insufficient evidence: no enough information to see if the jobs ads requires software development or not
        2. None: no software development required
        3. Some: some software development required
        4. Most: mainly software development
    For the rest it transform the different category into numerical value
        . None: 0
        . Some: 1
        . Most: 2
    From there, the mean is calculated. and from the result the three category are recreated
        . [0, 0.33, 0.5]: None
        . [0.6, 1]: Some
        . > 1: Most
    If there is one insufficient information among the tags, it negative the mean. If there is a consensus of Insufficient
    Information it gives a -10

    :params:
        df: containing the columns to compute
    :return:
        a panda Series with the computated mean
    """
    list_values = list()
    insufficient = 0
    for r in row:
        if r == 'No':
            list_values.append(0)
        elif r == 'Some':
            list_values.append(1)
        elif r == 'Most':
            list_values.append(2)
        elif r == 'Insufficient Evidence':
            insufficient +=1
        else:
            pass
    if insufficient > 1:
        return -10
    elif insufficient == 1:
        if len(list_values) == 1:
            return -0
        elif len(list_values) == 0:
            return -10
        else:
            return (-(sum(list_values) / float(len(list_values))))/2
    else:
        if len(list_values) == 1:
            return 0
        else:
            return (sum(list_values) / float(len(list_values)))/2

def corresponding_prev_train(col):
    for c in col:
        try:
            if int(col[0]) == int(col[1]):
                return 1
            else:
                return 0
        except ValueError:
            return col[0]


def new_tags(row):
    insuff = 0
    no = 0
    some = 0
    most = 0
    for r in row:
        if r == 'No':
            no +=1
        elif r == 'Some':
            some +=1
        elif r == 'Most':
            most +=1
        elif r == 'Insufficient Evidence':
            insuff +=1
        else:
            pass
    if insuff >= 2:
        return 'Insufficient Evidence'
    elif no >=2:
        return 'No'
    elif some >=2:
        return 'Some'
    elif most >= 2:
        return 'Most'
    elif no == 1 and some ==1 and most == 0:
        return 'No'
    elif no ==1 and most ==1 and some == 0:
        return  'Some'
    elif some == 1 and most ==1 and no == 0:
        return 'Some'
    elif no == 1 and some == 1 and most == 1:
        return 'Insufficient Evidence'
    elif insuff ==1 and some ==1 and most ==1:
        return 'Some'
    elif insuff ==1 and no ==1 and most == 1:
        return 'Insufficient Evidence'
    elif insuff ==1 and some ==1 and no ==1:
        return 'No'

def new_tag_agg(score):
    """
    Create a new tag with more category than before, adding insufficient, Some.
    at the end, there are 4 categories
    1. Insufficient evidence: score == -10
    2. No: abs(0.2) < score < abs(0.6)
    3. Some:
    4. Most: abs(0.6) < score <=1
    """
    if score == -10:
        return 'Insufficient'
    elif abs(score) >=0 and abs(score) < 0.2:
        return 'No'
    elif abs(score) >= 0.2 and abs(score) < 0.6:
        return 'Some'
    elif abs(score) > 0.6 and abs(score) <= 1:
        return 'Most'

def transform_df(df):
    """
    Collection of transformation that were initially in a jupyter notebook
    Here, it is a copy-paste, need a proper cleaning #TODO
    """
    #Splitting the lists into separated columns
    # tags
    tags = pd.DataFrame(df['tags'].values.tolist())
    tags.columns = ['tags_{}'.format(str(int(x)+1)) for x in tags.columns]
    subjects = pd.DataFrame(df['subject_area'].values.tolist())
    subjects.columns = ['subject_{}'.format(str(int(x)+1)) for x in subjects.columns]
    df = pd.concat([df, tags, subjects], axis=1, sort=False)
    # Create a columns with the number of existing tags
    df['tag_count'] = df[tags.columns].count(axis=1)
    # Drop rows that have only one tag
    df = df[df['tag_count'] > 1]
    df['agg_tags'] = df.loc[:, ['tags_1', 'tags_2', 'tags_3']].apply(calculate_score, axis=1)
    df['aggregate_tags'] = df['agg_tags'].apply(lambda x: 1 if abs(x)>=.5 and abs(x) < 10 else 0)
    df['multi_agg_tags'] = df.loc[:, 'agg_tags'].apply(new_tag_agg)
    df['consensus_tags'] = df.loc[:, ['tags_1', 'tags_2', 'tags_3', 'run_tag']].apply(previous_tags, axis=1)
    df['diff_consensus_tags'] = df.loc[:, ['tags_1', 'tags_2', 'tags_3']].apply(new_tags, axis=1)
    # df['corresponding_prev_tags'] = df.loc[:, ['consensus_tags', 'prediction']].apply(corresponding_prev_train, axis=1)

    return df


def save_df(df):
    # df.to_csv('./data/training_set/training_set.csv')
    path_to_df = './data/training_set/training_set.pkl'
    df.to_pickle(path_to_df)


if __name__ == "__main__":

    description='Get the tags from the mysql database'

    arguments = getArgs(description)
    config_values = arguments.return_arguments()

    db_conn = connectMongo(config_values)
    # set up access credentials
    df = get_training_set(db_conn, 'jobs')
    df = transform_df(df)

    save_df(df)
