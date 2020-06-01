#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pandas as pd
import numpy as np
from .common.getConnection import connectMongo
from .logger import logger
from .common.lib import isotime_snapshot
from .snapshots import ModelSnapshot

logger = logger(name='predict', stream_level='DEBUG')

class Bootstrap:
    """Get bootstrap means and confidence intervals from a sample.

    Parameters
    ----------
    random_state : int
        Set initial random state
    n : int, default=1000
        Number of bootstrap samples
    """
    def __init__(self, random_state, n=1000):
        self.random_state = random_state
        self.n = n

    def _single_sample_mean(self, array, random_state):
        np.random.seed(self.random_state + random_state)
        return np.random.choice(array, len(array)).mean()

    def sample(self, array):
        """Get bootstrap samples from array.

        Parameters
        ----------
        array : array-like
            Sample to perform bootstrap on

        Returns
        -------
        dict
            Dictionary containing probability, lower_ci, upper_ci
            (95% confidence intervals).
        """
        bootstrap_means = np.array([
            self._single_sample_mean(array, k)
            for k in range(self.n)
        ])
        return {
            'probability': bootstrap_means.mean(),
            'lower_ci': np.percentile(bootstrap_means, 2.5),
            'upper_ci': np.percentile(bootstrap_means, 97.5)
        }


class Predict:
    """Predict job classification using saved model snapshots.

    Parameters
    ----------
    model_snapshot : str
        Model snapshot to use for prediction
    random_state : int, default=0
        Random state, passed to :class:`Bootstrap` instance
    bootstrap_size : int, default=1000
        Number of bootstrap draws, passed to :class:`Bootstrap` instance
    """

    def __init__(self, model_snapshot, random_state=0, bootstrap_size=1000):
        self.model_snapshot = ModelSnapshot(model_snapshot)
        self.bootstrap = Bootstrap(random_state, bootstrap_size)
        self.config = self.model_snapshot.metadata['config']
        self.db = self._connect_db()
        self._predictions = []

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
        for doc in self.db['jobs'].find(
                {}, {'job_title': True, 'description': True,
                     'jobid': True}).batch_size(5):
            _id = doc['_id']
            try:
                doc = pd.DataFrame({'description': [doc['description']],
                                   'job_title': [doc['job_title']]})
            except KeyError:
                doc = None
            yield _id, doc

    def _record_prediction(self, _id, record):
        """Record the prediction in the original document in Mongodb.

        Parameters
        ----------
        _id : str
            Job ID to record
        record : dict
            Dictionary containing prediction information to save
            in database
        """
        record['snapshot'] = self.model_snapshot.name
        self._predictions.append(record)
        self.db['predictions'].update({'_id': _id + '_' + self.model_snapshot_name},
                                      {'$set': record})

    def predict(self, save=True):
        """Record predictions in MongoDB

        Parameters
        ----------
        save : bool, default=True
            Whether to save results in model snapshot folder, on by default.
            Results are always saved in the MongoDB instance

        Returns
        -------
        self : :class:`Predict`
            Returns copy of itself
        """
        ids_list = []
        for _id, doc in self._get_documents():
            if doc is not None:
                X = self.features.transform(doc)
                ids_list.append()
                probabilities = [
                    m.predict_proba(X) for
                    m in self.model_snapsdot.data.models
                ]
                self._record_prediction(_id, self.bootstrap.sample(probabilities))
        if save:
            self.save()
        return self

    def save(self, output=None):
        "Save predictions in model snapshot folder"
        with (self.model_snapshot.path / ('predict_%s.json' %
              isotime_snapshot())).open('w') as fp:
            for r in self._predictions:
                fp.write(json.dumps(r, sort_keys=True))

    @property
    def dataframe(self):
        "Returns predictions as pd.DataFrame"
        return pd.DataFrame(self._predictions)
