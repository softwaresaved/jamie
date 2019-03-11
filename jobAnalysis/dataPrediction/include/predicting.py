#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))


import pandas as pd

from common.logger import logger
from common.getConnection import connectMongo

__author__  = "Olivier Philippe"

"""
Take a feature pipeline and a model and predict new entry in the mongodb
Return the prediction as 1-0 and the probability and update the document with
the prediction
"""

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
        self.db = _connect_db()

    def _connect_db(self):
        """
        connect to the db

        return:
        ------
            db Mongodb(): connection to the specific collection
        """
        return connectMongo(config_values)

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
        if oversampling is True:
            predicting_field = 'prediction_{}_oversampling'.format(self.prediction_field)
        else:
            predicting_field = 'prediction_{}_oversampling'.format(self.prediction_field)
        if relaunch is True:
            search = {}
        else:
            search = {prediction_field: {'$exists': False}}
        for doc in db_conn['jobs'].find(search, {'job_title': True, 'description': True, 'jobid': True}).batch_size(5):
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
        return self.model.predict(X_to_predict), self.model.predict_proba(X_to_predict)

    def _extract_prediction(self, pred_int, pred_proba):
        """
        Extract the unique classification and the proba for that classification
        Right now, only tested for binary classification. If multilabel is used,
        need to test it. #TODO
        """
        return int(prediction[0]), float(predict_proba[0][0])

    def _record_prediction(self, _id, pred_int, pred_proba):
        """
        Record the prediction in the original document in Mongodb
        params:
        -------
            _id ObjectID(): document id to update
            pred_int int(): class of given by the prediction
            pred_proba float(): float of the probability of prediction
        """
        if oversampling is True:
            predicting_field = 'prediction_{}_oversampling'.format(self.prediction_field)
        else:
            predicting_field = 'prediction_{}_oversampling'.format(self.prediction_field)
        self.db['jobs'].update({'_id': _id}, {'$set': {prediction_field: pred_int
                                                       '{}_proba'.format(prediction_field): pred_proba}})

    def predict(self):
        for _id, doc in self._get_documents(self.relaunch):
            if doc:
                X = self._prepare_X(doc)
                pred_int, pred_proba = self._predict(X)
                pred_int, pred_proba = self._extract_prediction(pred_int, pred_proba)
            else:
                pred_int, pred_proba = None, None
            self._record_prediction(_id, pred_int, pred_proba)


def main():
    pass


if __name__ == "__main__":
    main()
