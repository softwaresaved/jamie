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


def main():

    description = 'Launch prediction modelling of jobs ads'

    arguments = getArgs(description)
    config_values = arguments.return_arguments()
    prediction_field = config_values.prediction_field

    # Create the folder if not existing
    directory = '../../outputs/dataPrediction/prediction/{}/'.format(prediction_field)
    if not os.path.exists(directory):
        os.makedirs(directory)

    logger.info('Starting the predictions')
    final_model, features, best_model_params = get_model(config_values.relaunch_model, prediction_field)
    if config_values.record_prediction is True:
        from include.predicting import Predict
        predict = Predict(config_values, prediction_field, features, final_model, config_values.relaunch)
        predict.run()
        final_count = dict()

        logger.info('Summary of prediction for new jobs')
        for k in final_count:
            logger.info('  Number of job classified as {}: {}'.format(k, final_count[k]))


if __name__ == "__main__":
    main()
