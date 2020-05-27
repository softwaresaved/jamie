#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import numpy as np
from .common.getConnection import connectMongo
from .logger import logger
from .snapshot import ModelSnapshot

logger = logger(name='predict', stream_level='DEBUG')

class Predict:
    """Predict job classification using saved model snapshots.

    Parameters
    ----------
    model_snapshot : str
        Model snapshot to use for prediction
    oversampling : bool, optional
        Whether to use oversampling to balance dataset, True by default
    """

    def __init__(self, model_snapshot):
        self.model_snapshot = ModelSnapshot(self.model_snapshot)
        self.model = self.model_snapshot.data.model
        self.config = self.model_snapshot.metadata['config']
        self.db = self._connect_db()

    def _connect_db(self):
        return connectMongo(self.config)

    def _get_documents(self):
        """Query the collection and return the documents for prediction as
        dataframe with the job_title and description field.

        Yields
        ------
        _id : ObjectID
            Unique id from the document, provided by MongoDB
        doc : pd.Dataframe
            Dataframe containing the description and job_title field. None if KeyError
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

    def _record_prediction(self, _id, pred_int, pred_proba):
        "Record the prediction in the original document in Mongodb"
        if self.oversampling is True:
            predicting_field = 'prediction_{}_oversampling'.format(self.prediction_field)
        else:
            predicting_field = 'prediction_{}'.format(self.prediction_field)
        self.db['jobs'].update({'_id': _id}, {'$set': {predicting_field: pred_int,
                                                       '{}_proba'.format(predicting_field): pred_proba}})

    def predict(self):
        "Record predictions in MongoDB"
        for _id, doc in self._get_documents(self.relaunch):
            if doc is not None:
                X = self.features.transform(doc)
                pred_int = self.model.predict(X)
                pred_proba = self.model.predict_proba(X)
                pred_int, pred_proba = self.model.predict(X), self.model.predict_proba(K
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
