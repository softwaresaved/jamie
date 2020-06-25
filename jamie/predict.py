#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import pandas as pd
import numpy as np
import json
from tqdm import tqdm
from bson.json_util import dumps
from .common.getConnection import connectMongo
from .logger import logger
from .common.lib import isotime_snapshot
from .snapshots import ModelSnapshot

Date = datetime.date

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
            _id = doc['jobid']
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
        record.update({
            'snapshot': self.model_snapshot.name,
            'jobid': _id,
            '_id': _id + '_' + self.model_snapshot.name
        })
        self.db.predictions.update_one({'_id': record['_id']}, {'$set': record}, upsert=True)
        job = self.db.jobs.find_one({'jobid': _id})
        if job:
            record.update(job)
            record['_id'] = _id + '_' + self.model_snapshot.name  # fix _id as it's overwritten
            if 'json' in record:
                del record['json']['description']  # remove verbose attributes
            del record['description']  # remove verbose attributes
            self._predictions.append(record)
        else:
            logger.info("Job not found in database, but prediction exists: {}".format(_id))

    def predict(self, save=True, skip_existing=True):
        """Record predictions in MongoDB

        Parameters
        ----------
        save : bool, default=True
            Whether to save results in model snapshot folder, on by default.
            Results are always saved in the MongoDB instance
        skip_existing : bool, default=True
            Whether to skip existing predictions or overwrite them. You can set
            this to False to force prediction of the entire dataset. Note that different
            model snapshots correspond to different prediction snapshots.

        Returns
        -------
        self : :class:`Predict`
            Returns copy of itself
        """
        ids_list = []
        models = [self.model_snapshot.model(i) for i in self.model_snapshot.data.indices]
        features = [self.model_snapshot.features(i) for i in self.model_snapshot.data.indices]
        for _id, doc in tqdm(self._get_documents(), desc="Predicting"):
            if doc is not None:
                # Check if it has already been predicted
                if skip_existing and self.db.predictions.find_one(
                        {'_id': _id + '_' + self.model_snapshot.name}):
                    continue
                ids_list.append(_id)
                probabilities = [
                    # predict_proba() returns a tuple for class (0, 1)
                    # we need the probability that class is 1, so we select
                    # the second element
                    m.predict_proba(f.transform(doc))[0][1]
                    for m, f in zip(models, features)
                ]
                self._record_prediction(_id, self.bootstrap.sample(probabilities))
        if save:
            self.save()
        return self

    def save(self, output=None):
        "Save predictions in prediction snapshot folder"
        snapshot_root = self.model_snapshot.path.parent.parent \
            / 'predictions' / isotime_snapshot()
        if not snapshot_root.exists():
            snapshot_root.mkdir(parents=True)
        with (snapshot_root / 'predictions.jsonl').open('w') as fp:
            for r in self._predictions:
                fp.write(dumps(r, sort_keys=True) + "\n")
        with (snapshot_root / 'metadata.json').open('w') as fp:
            metadata = self.model_snapshot.metadata
            metadata['best_model_average_score'] = self.model_snapshot.data.scores.mean(axis=1).max()
            json.dump(self.model_snapshot.metadata, fp, indent=True, sort_keys=True)

    @property
    def dataframe(self):
        "Returns predictions as pd.DataFrame"
        return pd.DataFrame(self._predictions)
