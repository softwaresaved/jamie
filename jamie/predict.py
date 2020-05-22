#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import numpy as np
from sklearn.externals.joblib import dump, load
from .common.getConnection import connectMongo
from .logger import logger

logger = logger(name='prediction_run', stream_level='DEBUG')

class Predict:

    def __init__(self, config_values, prediction_field, features, model, oversampling, relaunch=False):
        """
        params:
        ------
            config_values dict(): values from the config.py file in ../config/
            prediction_field str(): the name of the prediction to make
            feature Pipeline(): of different transformation to do on the document as defined
                in feature.py
            model sklearn.model: the model to use for prediction
            relaunch boo(): if had to redo all the prediction or not (Default=False)
        return:
        -------
             None
        """
        self.config_values = config_values
        self.prediction_field = prediction_field
        self.features = features
        self.model = model
        self.oversampling = oversampling
        self.relaunch = relaunch
        self.db = self._connect_db()

    def _connect_db(self):
        """
        connect to the db

        return:
        ------
            db Mongodb(): connection to the specific collection
        """
        return connectMongo(self.config_values)

    def _get_documents(self, relaunch=False):
        """
        Query the collection and return the documents for prediction as dataframe with the job_title and description
        field
        params:
        -------
            relaunch bool(): Decide if return all documents or only documents that does not have a prediction
        return:
        ------
            _id ObjectID(): the unique id from the document, provided by MongoDB
            doc dataframe() -- None: the dataframe containing the description and job_title field. None if Keyerror
        """
        if self.oversampling is True:
            predicting_field = 'prediction_{}_oversampling'.format(self.prediction_field)
        else:
            predicting_field = 'prediction_{}'.format(self.prediction_field)
        if relaunch is True:
            search = {}
        else:
            search = {self.prediction_field: {'$exists': False}}
        for doc in self.db['jobs'].find(search, {'job_title': True, 'description': True, 'jobid': True}).batch_size(5):
            _id = doc['_id']
            try:
                doc =  pd.DataFrame({'description': [doc['description']], 'job_title': [doc['job_title']]})
            except KeyError:
                doc = None
            yield _id, doc

    def _prepare_X(self, df):
        """
        Transform X with the self.feature pipeline, prior to the prediction
        params:
        -------
            document str(): containing the information to transform
        return:
        -------
            transformed X: applied feature pipeline on the document
        """
        return self.features.transform(df)

    def _predict(self, X):
        """
        Classify the X documents
        params:
        -------
            X numpy array(): vector to predict
        returns:
        -------
            prediction numpy_array(): Class predicted
            pred_proba numpy_array(): probability of the prediction
        """
        return self.model.predict(X), self.model.predict_proba(X)

    def _extract_prediction(self, pred_int, pred_proba):
        """
        Extract the unique classification and the proba for that classification
        Right now, only tested for binary classification. If multilabel is used,
        need to test it. #TODO
        """
        return int(pred_int[0]), float(pred_proba[0][0])

    def _record_prediction(self, _id, pred_int, pred_proba):
        """
        Record the prediction in the original document in Mongodb
        params:
        -------
            _id ObjectID(): document id to update
            pred_int int(): class of given by the prediction
            pred_proba float(): float of the probability of prediction
        """
        if self.oversampling is True:
            predicting_field = 'prediction_{}_oversampling'.format(self.prediction_field)
        else:
            predicting_field = 'prediction_{}'.format(self.prediction_field)
        self.db['jobs'].update({'_id': _id}, {'$set': {predicting_field: pred_int,
                                                       '{}_proba'.format(predicting_field): pred_proba}})

    def predict(self):
        for _id, doc in self._get_documents(self.relaunch):
            if doc is not None:
                X = self._prepare_X(doc)
                pred_int, pred_proba = self._predict(X)
                pred_int, pred_proba = self._extract_prediction(pred_int, pred_proba)
            else:
                pred_int, pred_proba = None, None
            self._record_prediction(_id, pred_int, pred_proba)


def record_information(best_model_params,
                       final_model, feature_model,
                       y_test, y_pred, y_proba, directory):

    logger.info('Record the model information')
    np.save('{}{}'.format(directory, 'y_test'), y_test)
    np.save('{}{}'.format(directory, 'y_pred'), y_pred)
    np.save('{}{}'.format(directory, 'y_proba'), y_proba)

    with open('{}{}'.format(directory, 'best_model_params.json'), 'w') as f:
        json.dump(best_model_params, f)

def main():

    description = 'Launch prediction modelling of jobs ads'

    arguments = getArgs(description)
    config_values = arguments.return_arguments()
    prediction_field = config_values.prediction_field
    oversampling = config_values.oversampling
    scoring_value = config_values.prediction_metric
    nb_folds = config_values.k_fold
    # for prediction_field, oversampling, scoring_value in [('aggregate', True, 'f1_weighted'),
    #                                                       ('aggregate', False, 'f1_weighted'),
    #                                                       ('consensus', False, 'f1_weighted'),
    #                                                       ('consensus', True, 'f1_weighted')]:
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
