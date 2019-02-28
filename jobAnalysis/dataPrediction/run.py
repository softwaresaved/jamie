#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
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

from common.logger import logger
from common.getArgs import getArgs
from common.getConnection import connectMongo

logger = logger(name='prediction_run', stream_level='DEBUG')



def record_information(prediction_field, best_model_params,
                       final_model, feature_model,
                       y_test, y_pred, y_proba,
                       folder='../../outputs/dataPrediction/prediction/'):

    logger.info('Record the model information')
    np.save('{}{}/{}'.format(folder, prediction_field, 'y_test'), y_test)
    np.save('{}{}/{}'.format(folder, prediction_field, 'y_pred'), y_pred)
    np.save('{}{}/{}'.format(folder, prediction_field, 'y_proba'), y_proba)

    with open('{}{}/{}'.format(folder, prediction_field, 'best_model_params.json'), 'w') as f:
        json.dump(best_model_params, f)

def record_model(prediction_field, model, features, folder='../../outputs/dataPrediction/prediction/'):
    """
    """
    joblib.dump(features, '{}{}/{}'.format(folder, prediction_field, 'features.pkl'))
    joblib.dump(model, '{}{}/{}'.format(folder, prediction_field, 'model.pkl'))


def load_model(prediction_field, folder='../../outputs/dataPrediction/prediction/'):
    features = joblib.load('{}{}/{}'.format(folder, prediction_field, 'features.pkl'))
    model = joblib.load('{}{}/{}'.format(folder, prediction_field, 'model.pkl'))
    return features, model


def load_info_model(prediction_field, folder='../../outputs/dataPrediction/prediction/'):
    with open('{}{}/{}'.format(folder, prediction_field, 'best_model_params.json')) as handle:
        best_model_params = json.loads(handle.read())
    return best_model_params


def get_model(relaunch, prediction_field):

    if relaunch is True:

        X_train, X_test, y_train, y_test, features = get_train_data(prediction_field)
        X_train = features.fit_transform(X_train)

        best_model_params, final_model = nested_cross_validation(X_train, y_train, prediction_field, nbr_folds=2)

        X_test = features.transform(X_test)
        y_pred = final_model.predict(X_test)
        y_proba = final_model.predict_proba(X_test)

        record_model(prediction_field, final_model, features)
        record_information(prediction_field, best_model_params, final_model, features,
                           y_test, y_pred, y_proba)

    elif relaunch is False:
        features, final_model = load_model(prediction_field)
        best_model_params = load_info_model(prediction_field)

    else:
        raise('Not a proper command argument')

    return final_model, features, best_model_params


def predicting(db_conn, prediction_field, features, model, relaunch):
    predicting_field = 'prediction_{}'.format(prediction_field)
    if relaunch is True:
        search = {}
    else:
        search = {prediction_field: {'$exists': False}}
    for doc in db_conn['jobs'].find(search, {'job_title': True, 'description': True, 'jobid': True}).batch_size(5):
        _id = doc['_id']
        jobid = doc['jobid']
        try:
            df = pd.DataFrame({'description': [doc['description']], 'job_title': [doc['job_title']]})
            X_to_predict = features.transform(df)
            prediction = model.predict(X_to_predict)
            predic_proba = model.predict_proba(X_to_predict)
        except KeyError:
            prediction = None
            predic_proba = None

        yield jobid, prediction, predic_proba, _id


def record_prediction(db, prediction_field, prediction, predict_proba, jobid, _id, model_best_params):
    """
    """
    if jobid is None:
        return
    if prediction is None:
        pred_int = 'None'
        pred_proba = 'None'
    else:
        pred_int = int(prediction[0])

        pred_proba = float(predict_proba[0][0])

    # db['predictions'].update({'jobid': jobid,
    #                         'params': model_best_params},
    #                          {'$set': {prediction_field: pred_int, '{}_proba'.format(prediction_field): pred_proba}},
    #                         upsert=True)
    db['jobs'].update({'_id': _id}, {'$set': {prediction_field: pred_int, '{}_proba'.format(prediction_field): pred_proba}})
    return pred_int


def main():

    description = 'Launch prediction modelling of jobs ads'

    arguments = getArgs(description)
    config_values = arguments.return_arguments()
    prediction_field = config_values.prediction_field
    logger.info('Starting the predictions')
    final_model, features, best_model_params = get_model(config_values.relaunch_model, prediction_field)
    if config_values.record_prediction is True:
        final_count = dict()
        db_conn = connectMongo(config_values)
        db_conn['predictions'].create_index('jobid', unique=False)
        db_conn['predictions'].create_index('{}'.format(prediction_field), unique=False)
        for job_id, prediction, predic_proba, _id in predicting(db_conn, prediction_field, features, final_model, config_values.relaunch_prediction):
            if prediction == None:
                to_record = 'None'
            else:
                to_record = str(prediction[0])
            final_count[to_record] = final_count.get(to_record, 0)+1

            record_prediction(db_conn, prediction_field, prediction, predic_proba, job_id, _id, best_model_params)

        logger.info('Summary of prediction for new jobs')
        for k in final_count:
            logger.info('  Number of job classified as {}: {}'.format(k, final_count[k]))



if __name__ == "__main__":
    main()
