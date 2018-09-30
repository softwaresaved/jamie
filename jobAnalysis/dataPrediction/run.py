#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import argparse
import json

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from io import StringIO

import pandas as pd
import numpy as np


from include.features import get_train_data
from include.model import nested_cross_validation

from sklearn.metrics import confusion_matrix
from sklearn.externals import joblib

from common.getConnection import connectDB
from common.logger import logger

logger = logger(name='prediction_run', stream_level='DEBUG')



def record_information(best_model_name, best_model_params,
                       final_model, feature_model,
                       y_test, y_pred, y_proba,
                       folder='../../outputs/dataPrediction/'):

    print(y_test)
    np.save('{}{}'.format(folder, 'y_test'), y_test)
    print(y_pred)
    np.save('{}{}'.format(folder, 'y_pred'), y_pred)
    print(y_proba)
    np.save('{}{}'.format(folder, 'y_proba'), y_proba)
    print(best_model_params)


def record_model(model, features, folder='../../outputs/dataPrediction'):
    """
    """
    joblib.dump(features, '{}{}'.format(folder, 'features.pkl'))
    joblib.dump(model, '{}{}'.format(folder, 'model.pkl'))


def load_model(folder='../../outputs/dataPrediction/'):
    features = joblib.load('{}{}'.format(folder, 'features.pkl'))
    model = joblib.load('{}{}'.format(folder, 'model.pkl'))
    return features, model


def load_info_model(folder='../../outputs/dataPrediction/'):
    with open('{}{}'.format(folder, 'best_model_params.json')) as handle:
        best_model_params = json.loads(handle.read())
    with open('{}{}'.format(folder, 'best_model_name.txt', 'r')) as f:
        best_model_name = f.readline().strip()
    return best_model_name, best_model_params


def get_model(relaunch):

    if relaunch == 'True':

        X_train, X_test, y_train, y_test, features = get_train_data()
        X_train = features.fit_transform(X_train)

        best_model_name, best_model_params, final_model = nested_cross_validation(X_train, y_train)

        X_test = features.transform(X_test)
        y_pred = final_model.predict(X_test)
        y_proba = final_model.predict_proba(X_test)

        record_model(final_model, features)
        record_information(best_model_name, best_model_params, final_model, features,
                           y_test, y_pred, y_proba)

    elif relaunch == 'False':
        features, final_model = load_model()
        best_model_name, best_model_params = load_info_model()

    else:
        raise('Not a proper command argument')

    return final_model, features, best_model_name, best_model_params



def predicting(db_conn, features, model, relaunch):

    if relaunch == 'True':
        search = {}
    elif relaunch == 'False':
        search = {'prediction': {'$exists': False}}
    for doc in db_conn['jobs'].find(search, {'job_title': True, 'description': True, 'jobid': True}).batch_size(5):
        _id = doc['_id']
        jobid = doc['jobid']
        try:
            df = pd.DataFrame({'description': [doc['description']], 'job_title': [doc['job_title']]})
            X_to_predict = features.transform(df)
            prediction = model.predict(X_to_predict)
        except KeyError:
            prediction = None

        yield jobid, prediction, _id


def record_prediction(db, prediction, jobid, _id, model_name, model_best_params):
    """
    """
    if jobid is None:
        return
    if prediction is None:
        prediction = 'None'
    else:
        prediction = int(prediction[0])
    # if prediction[0] == 0:
    #     prediction = 'No'
    # if prediction[0] == 1:
    #     prediction = 'Yes'
    print(prediction)
    # print('model - type: {} - value: {}'.format(type(model_name), model_name))
    # print('model best params - type: {}  - values: {}'.format(type(model_best_params), model_best_params))
    # print('prediction - type: {} - value: {}'.format(type(prediction), prediction))

    db['predictions'].update({'jobid': jobid,
                              'model': model_name},
                            # 'params': model_best_params},
                            {'$set': {'prediction': prediction}},
                            upsert=True)
    db['jobs'].update({'_id': _id}, {'$set': {'prediction': prediction}})


def main():

    parser = argparse.ArgumentParser(description='Launch prediction modelling of jobs ads')

    parser.add_argument('-r', '--relaunch',
                        type=str,
                        default='False',
                        help='Decide if rerun the modelling or pickle the existing one if exists. Default value is false')
    parser.add_argument('-c', '--config',
                        type=str,
                        default='config_dev.ini')

    args = parser.parse_args()
    config_file = '../config/'+args.config
    db_conn = connectDB(config_file)
    db_conn['predictions'].create_index('jobid', unique=True)
    db_conn['predictions'].create_index('prediction', unique=False)

    final_model, features, best_model_name, best_model_params = get_model(args.relaunch)
    for job_id, prediction, _id in predicting(db_conn, features, final_model, args.relaunch):
        record_prediction(db_conn, prediction, job_id, _id, best_model_name, best_model_params)



if __name__ == "__main__":
    main()
