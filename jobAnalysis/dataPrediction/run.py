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
from include.predicting import Predict

from sklearn.metrics import confusion_matrix
from sklearn.externals import joblib

from common.logger import logger
from common.getArgs import getArgs

logger = logger(name='prediction_run', stream_level='DEBUG')


def record_information(best_model_params,
                       final_model, feature_model,
                       y_test, y_pred, y_proba,
                       foldername,
                       folder='../../outputs/dataPrediction/prediction/'):

    logger.info('Record the model information')
    np.save('{}{}/{}'.format(folder, foldername, 'y_test'), y_test)
    np.save('{}{}/{}'.format(folder, foldername, 'y_pred'), y_pred)
    np.save('{}{}/{}'.format(folder, foldername, 'y_proba'), y_proba)

    with open('{}{}/{}'.format(folder, foldername, 'best_model_params.json'), 'w') as f:
        json.dump(best_model_params, f)


def record_model(model, features, foldername, folder='../../outputs/dataPrediction/prediction/'):
    """
    """
    joblib.dump(features, '{}{}/{}'.format(folder, foldername, 'features.pkl'))
    joblib.dump(model, '{}{}/{}'.format(folder, foldername, 'model.pkl'))


def load_model(foldername, folder='../../outputs/dataPrediction/prediction/'):
    features = joblib.load('{}{}/{}'.format(folder, foldername, 'features.pkl'))
    model = joblib.load('{}{}/{}'.format(folder, foldername, 'model.pkl'))
    return features, model


def load_info_model(foldername, folder='../../outputs/dataPrediction/prediction/'):
    with open('{}{}/{}'.format(folder, foldername, 'best_model_params.json')) as handle:
        best_model_params = json.loads(handle.read())
    return best_model_params


def get_model(relaunch, nbr_folds, prediction_field, oversampling):

    foldername = _foldername(prediction_field, oversampling)
    if relaunch is True:

        X_train, X_test, y_train, y_test, features = get_train_data(prediction_field)
        X_train = features.fit_transform(X_train)

        best_model_params, final_model = nested_cross_validation(X_train, y_train, prediction_field, oversampling, nbr_folds=nbr_folds)

        X_test = features.transform(X_test)
        y_pred = final_model.predict(X_test)
        y_proba = final_model.predict_proba(X_test)

        record_model(final_model, features, foldername)
        record_information(best_model_params, final_model, features,
                           y_test, y_pred, y_proba, foldername)

    elif relaunch is False:
        features, final_model = load_model(foldername)
        best_model_params = load_info_model(foldername)

    else:
        raise('Not a proper command argument')

    return final_model, features, best_model_params


def _foldername(prediction_field, oversampling):

    if oversampling:
        foldername = '{}_oversampling'.format(prediction_field)
    else:
        foldername = prediction_field
    return foldername

def main():

    description = 'Launch prediction modelling of jobs ads'

    arguments = getArgs(description)
    config_values = arguments.return_arguments()
    prediction_field = config_values.prediction_field
    oversampling = config_values.oversampling
    foldername = _foldername(prediction_field, oversampling)

    # Create the folder if not existing
    directory = '../../outputs/dataPrediction/prediction/{}/'.format(foldername)
    if not os.path.exists(directory):
        os.makedirs(directory)

    logger.info('Starting the predictions')
    final_model, features, best_model_params = get_model(config_values.relaunch_model, config_values.k_fold, prediction_field, oversampling)
    if config_values.record_prediction is True:
        from include.predicting import Predict
        predict = Predict(config_values, prediction_field, features, final_model, oversampling, config_values.relaunch_model)
        predict.predict()
        final_count = dict()

        logger.info('Summary of prediction for new jobs')
        for k in final_count:
            logger.info('  Number of job classified as {}: {}'.format(k, final_count[k]))


if __name__ == "__main__":
    main()
