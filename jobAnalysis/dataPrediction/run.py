#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

# from io import StringIO

import numpy as np

from include.features import get_train_data
from include.model import nested_cross_validation
from include.predicting import Predict

from sklearn.externals import joblib

from common.logger import logger
from common.getArgs import getArgs

logger = logger(name='prediction_run', stream_level='DEBUG')


def record_information(best_model_params,
                       final_model, feature_model,
                       y_test, y_pred, y_proba, directory):

    logger.info('Record the model information')
    np.save('{}{}'.format(directory, 'y_test'), y_test)
    np.save('{}{}'.format(directory, 'y_pred'), y_pred)
    np.save('{}{}'.format(directory, 'y_proba'), y_proba)

    with open('{}{}'.format(directory, 'best_model_params.json'), 'w') as f:
        json.dump(best_model_params, f)


def record_model(model, features, directory):
    """
    """
    joblib.dump(features, '{}{}'.format(directory, 'features.pkl'))
    joblib.dump(model, '{}{}'.format(directory, 'model.pkl'))


def record_average_scores(scores, nbr_folds, directory):
    """
    Record the result of each outer_cv loop into a panda df and
    then record it into a csv.
    Before saving it checks if a similar csv file exists to append it instead
    of overwritting it.
    The name is based on the method to folds and just write the different models unders
    """
    filename = directory +'average_scores_' + nbr_folds + '.csv'
    scores.to_csv(filename)


def load_model(directory):
    features = joblib.load('{}{}'.format(directory, 'features.pkl'))
    model = joblib.load('{}{}'.format(directory, 'model.pkl'))
    return features, model


def load_info_model(directory):
    with open('{}{}'.format(directory, 'best_model_params.json')) as handle:
        best_model_params = json.loads(handle.read())
    return best_model_params


def get_model(relaunch, nbr_folds, prediction_field, scoring_value, oversampling, directory):

    if relaunch is True:

        X_train, X_test, y_train, y_test, features = get_train_data(prediction_field)
        X_train = features.fit_transform(X_train)

        best_model_params, final_model, average_scores = nested_cross_validation(X_train, y_train, prediction_field, scoring_value, oversampling, nbr_folds=nbr_folds)

        X_test = features.transform(X_test)
        y_pred = final_model.predict(X_test)
        y_proba = final_model.predict_proba(X_test)

        record_model(final_model, features, directory)
        record_information(best_model_params, final_model, features,
                           y_test, y_pred, y_proba, directory)
        record_average_scores(average_scores, nbr_folds, directory)

    elif relaunch is False:
        features, final_model = load_model(directory)
        best_model_params = load_info_model(directory)

    else:
        raise('Not a proper command argument')

    return final_model, features, best_model_params


def _create_directory(prediction_field, scoring_value, oversampling):

    root_folder = '../../outputs/dataPrediction/prediction/'
    if oversampling:
        directory = root_folder + prediction_field + '_' + scoring_value + '_oversampling' + '/'
    else:
        directory = root_folder + prediction_field + + '_' + scoring_value + '/'

    # check folder if exists otherwise create it

    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def main():

    description = 'Launch prediction modelling of jobs ads'

    arguments = getArgs(description)
    config_values = arguments.return_arguments()
    prediction_field = config_values.prediction_field
    oversampling = config_values.oversampling
    scoring_value = config_values.prediction_metric
    nb_folds = config_values.k_fold

    # Create the folder if not existing
    directory = _create_directory(prediction_field, scoring_value, oversampling)

    logger.info('Starting the predictions')
    final_model, features, best_model_params = get_model(config_values.relaunch_model, nb_folds, prediction_field, scoring_value, oversampling, directory)
    if config_values.record_prediction is True:
        predict = Predict(config_values, prediction_field, features, final_model, oversampling, config_values.relaunch_model)
        predict.predict()
        final_count = dict()

        logger.info('Summary of prediction for new jobs')
        for k in final_count:
            logger.info('  Number of job classified as {}: {}'.format(k, final_count[k]))


if __name__ == "__main__":
    main()
