__version__ = '0.1'

import json
import collections
import pandas as pd
from pathlib import Path
import jamie.config
import jamie.scrape
import jamie.snapshots
import jamie.models
import jamie.features
import jamie.data
import jamie.data.importer
import jamie.predict
import jamie.reports
from jamie.common.information_gain import _information_gain
from jamie.common.getConnection import connectMongo

class Jamie:
    """Job Analysis by Machine Information Extraction"""

    def __init__(self, config=None):
        if config:
            self.cf = jamie.config.Config(config)
        else:
            self.cf = jamie.config.Config()

    def version(self):
        "Version information for jamie"
        return __version__

    def employers(self):
        "List possible employer sets"
        return jamie.data.list_employers()

    def load(self, employer=None):  # NOQA
        "Read scraped jobs into MongoDB"
        if employer:
            jamie.data.importer.main(self.cf, employer=employer)
        else:
            jamie.data.importer.main(self.cf)

    def config(self, field=None, value=None):
        "Reads and sets jamie configuration"
        return jamie.config.configurator(field, value)

    def scrape(self):
        "Scrapes jobs from jobs.ac.uk"
        return jamie.scrape.main(self.cf)

    def snapshots(self, kind, instance=None):
        "Show saved snapshots (models/training)"
        return jamie.snapshots.main(kind, instance)

    def readjob(self, fn, save=False):
        "Reads a job HTML and prints in JSON format, with option to save"
        data = json.dumps(
            jamie.scrape.JobFile(Path(fn)).parse().json, indent=2, sort_keys=True)
        if save:
            (Path(fn).parent / (Path(fn).stem + '.json')).write_text(data)
        else:
            return data

    def features(self):
        "List possible features (job types)"
        return jamie.features.list_features()

    def train(self, snapshot='last', featureset='rse',
              models = None,
              prediction_field='aggregate_tags',
              oversampling=False, scoring='precision',
              random_state=100):
        "Train using specified snapshot (default: last)"
        ts = jamie.snapshots.TrainingSnapshotCollection(self.cf['common.snapshots'])
        if snapshot == 'last':
            snapshot = ts.most_recent()
        if models is not None:
            models = models.split(",")
        jamie.models.train(self.cf, snapshot, featureset, models, prediction_field,
                           oversampling, scoring, random_state)

    def predict(self, snapshot=None):
        "Predict using specified snapshot"
        if snapshot is None:
            model_snapshots = jamie.snapshots.ModelSnapshotCollection(
                self.cf['common.snapshots'])
            snapshot = model_snapshots.most_recent()
        print(jamie.predict.Predict(snapshot).predict().dataframe)

    def random_sample_prediction(self, snapshot=None,
                                 n_each_class=100, random_state=100):
        "Generates a random sample of positive and negative classes"
        fn = "random-sample_n{}_rnd{}.csv".format(n_each_class, random_state)
        db = connectMongo(self.cf)
        if snapshot is None:
            prediction_snapshots = jamie.snapshots.PredictionSnapshotCollection(
                self.cf['common.snapshots'])
            snapshot = jamie.snapshots.PredictionSnapshot(prediction_snapshots.most_recent())
        else:
            snapshot = jamie.snapshots.PredictionSnapshot(snapshot)
        positives, negatives = snapshot.partition_jobs(n_each_class, random_state)
        data = []

        def find_description(jobid):
            found = db.jobs.find_one({"jobid": jobid})
            return found.get('description', None) if found else None

        print("Fetching descriptions for positives...")
        for i in positives:
            i['is_target_job_type'] = True
            i['description'] = find_description(i['jobid'])
            data.append(i)
        print("Fetching descriptions for negatives...")
        for i in negatives:
            i['is_target_job_type'] = True
            i['is_target_job_type'] = False
            i['description'] = find_description(i['jobid'])
            data.append(i)

        pd.DataFrame(data).to_csv(snapshot.path / fn, index=False)
        return snapshot.path / fn

    def report(self, snapshot=None):
        "Generate report using specified snapshot"
        if snapshot is None:
            predictions = jamie.snapshots.PredictionSnapshotCollection(
                self.cf['common.snapshots'])
            snapshot = predictions.most_recent()
            jamie.reports.Report(jamie.snapshots.PredictionSnapshot(snapshot)).create()

    def information_gain(self, training_snapshot="last",
                         text_column="description", output_column="aggregate_tags"):
        "Calculates information gain for text ngrams in training snapshot"
        ts = jamie.snapshots.TrainingSnapshotCollection()
        if training_snapshot == "last":
            training_snapshot = ts.most_recent()
        return _information_gain(training_snapshot, text_column, output_column)

    def list_jobids(self):
        "List job ids from jobs database"
        db = connectMongo(self.cf)
        for i in db[self.cf['db.jobs']].find():
            print(i['jobid'])

    def distribution(self, kind):
        "Distribution of jobs in database: monthly or yearly"
        dist = collections.defaultdict(int)
        db = connectMongo(self.cf)
        for i in db[self.cf['db.jobs']].find():
            if 'placed_on' not in i:
                continue
            if kind == "monthly":
                dist["{:d}-{:02d}".format(i['placed_on'].year, i['placed_on'].month)] += 1
            else:
                dist[i['placed_on'].year] += 1
        data = pd.DataFrame(data=[(y, dist[y]) for y in sorted(dist)], columns=[kind[:-2], 'frequency'])
        print(data)
        print("Total:", data.frequency.sum())
