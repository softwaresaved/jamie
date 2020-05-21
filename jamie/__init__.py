__version__ = '0.1'

import jamie.config
import jamie.scrape
import jamie.snapshots
import jamie.models
import jamie.features
import jamie.data
import jamie.data.importer

class Jamie:
    """jamie: Job Analysis by Machine Information Extraction"""

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

    def snapshots(self, kind):
        "Show saved snapshots (models/training)"
        return jamie.snapshots.main(kind)

    def features(self):
        "List possible features (job types)"
        return jamie.features.list_features()

    def train(self, snapshot='last', featureset='rse',
              prediction_field='aggregate_tags',
              oversampling=True, scoring='precision'):
        "Train using specified snapshot (default: last)"
        ts = jamie.snapshots.TrainingSnapshot(self.cf['common.snapshots'])
        if snapshot == 'last':
            snapshot = ts.most_recent()
        jamie.models.train(self.cf, snapshot, featureset, prediction_field,
              oversampling, scoring)
