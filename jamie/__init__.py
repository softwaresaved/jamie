__version__ = '0.1'

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
            jamie.data.importer.main(employer=employer)
        else:
            jamie.data.importer.main()

    def config(self, field=None, value=None):
        "Reads and sets jamie configuration"
        return jamie.config.configurator(field, value)

    def scrape(self):
        "Scrapes jobs from jobs.ac.uk"
        return jamie.scrape.main()

    def snapshots(self, kind, instance=None):
        "Show saved snapshots (models/training)"
        return jamie.snapshots.main(kind, instance)

    def features(self):
        "List possible features (job types)"
        return jamie.features.list_features()

    def train(self, snapshot='last', featureset='rse',
              models = None,
              prediction_field='aggregate_tags',
              oversampling=False, scoring='f1',
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
