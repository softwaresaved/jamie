__version__ = "0.1"

import json
import collections
import pandas as pd
from pathlib import Path

import pymongo

import jamie.config
import jamie.scrape
import jamie.snapshots
import jamie.models
import jamie.features
import jamie.data
import jamie.data.importer
import jamie.predict
import jamie.reports
from jamie.information_gain import _information_gain
from jamie.lib import (
    connect_mongo,
    check_nltk_download,
    setup_messages,
    bullet_text as o,
    success,
    bold,
)

NLTK_DATA = ["stopwords", "punkt"]


class Jamie:
    """Job Analysis by Machine Information Extraction"""

    def __init__(self, config=None):
        if config:
            self.cf = jamie.config.Config(config)
        else:
            self.cf = jamie.config.Config()

    def setup(self):
        "Initial setup for Jamie"
        msgs = []
        try:
            db = connect_mongo(self.cf)
            count = db[self.cf["db.jobs"]].estimated_document_count()
            msgs.append((True, "Jobs database connection ({} jobs)".format(count)))
        except pymongo.errors.ServerSelectionTimeoutError:
            msgs.append((False, "Jobs database connection failed"))
        nltk_datasets_present = check_nltk_download(*NLTK_DATA)
        msgs.append(
            (
                nltk_datasets_present,
                "NLTK datasets {}".format(
                    nltk_datasets_present and "present" or "absent"
                ),
            )
        )
        ts = jamie.snapshots.TrainingSnapshotCollection()
        if (
            not ts.is_empty
            and (ts.latest().instance_location / "training_set.csv").exists()
        ):
            msgs.append((True, "Training set exists"))
        else:
            msgs.append(
                (False, "Training set not found, required to run 'jamie train'")
            )
        return setup_messages(msgs)

    def version(self):
        "Version information for jamie"
        return __version__

    def load(self, dry_run=False):  # NOQA
        "Read scraped jobs into MongoDB"
        folder = " " + str(self.cf["scrape.folder"])
        print(
            dry_run
            and (
                o("Checking for missing attributes from: " + folder)
                + "\n   This will not modify the database.\n"
            )
            or o("Loading jobs into database from:" + folder) + "\n"
        )
        njobs = jamie.data.importer.main(self.cf, dry_run=dry_run)
        print(
            njobs
            and success(
                "Loading complete, added {} jobs to database".format(njobs["inserted"])
            )
            or success("Check completed")
        )

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
        fn = Path(fn)
        if not fn.exists():
            return "[jamie readjob] File does not exist: " + str(fn)
        data = json.dumps(
            jamie.scrape.JobFile(fn).parse().json, indent=2, sort_keys=True
        )
        if save:
            (fn.parent / (fn.stem + ".json")).write_text(data)
        else:
            return data

    def features(self):
        "List possible features (job types)"
        return jamie.features.list_features()

    def train(
        self,
        snapshot=None,
        featureset="rse",
        models=None,
        prediction_field="aggregate_tags",
        oversampling=False,
        scoring="precision",
        random_state=100,
    ):
        "Train using specified snapshot (default: last)"
        ts = jamie.snapshots.TrainingSnapshotCollection(self.cf["common.snapshots"])
        snapshot = ts[snapshot] if snapshot else ts.latest()
        if models is not None:
            models = models.split(",")
        print(o("Training using snapshot: {}".format(snapshot.name)))
        print("\n   " + bold("Known warnings"))
        print("   --------------")
        print(
            """   scikit-learn shows UndefinedMetricWarning in cases when the precision
   or recall score is ill-defined, when there are no positive predictions,
   or no positive labels respectively. This can happen for small datasets,
   In the case of precision, a classifier that is conservative in
   predicting the positive class will often generate this warning. In these
   cases the score is set to zero.

   The problem can be resolved by choosing a large enough dataset, such
   that each of the cross-validation folds is large enough, or by choosing
   a metric that emphasies both precision and recall, such as f1 score.
   """
        )
        jamie.models.train(
            self.cf,
            snapshot,
            featureset,
            models,
            prediction_field,
            oversampling,
            scoring,
            random_state,
        )
        print(success("Training complete"))
        print("   Run prediction: jamie predict")

    def predict(self, snapshot=None):
        "Predict using specified snapshot"
        model_snapshots = jamie.snapshots.ModelSnapshotCollection(
            self.cf["common.snapshots"]
        )
        snapshot = model_snapshots[snapshot] if snapshot else model_snapshots.latest()
        print(jamie.predict.Predict(snapshot).predict().dataframe)

    def random_sample_prediction(
        self, snapshot=None, n_each_class=100, random_state=100
    ):
        "Generates a random sample of positive and negative classes"
        fn = "random-sample_n{}_rnd{}.csv".format(n_each_class, random_state)
        db = connect_mongo(self.cf)
        prediction_snapshots = jamie.snapshots.PredictionSnapshotCollection(
            self.cf["common.snapshots"]
        )
        snapshot = (
            prediction_snapshots[snapshot]
            if snapshot
            else prediction_snapshots.latest()
        )
        positives, negatives = snapshot.partition_jobs(n_each_class, random_state)
        data = []

        def find_description(jobid):
            found = db.jobs.find_one({"jobid": jobid})
            return found.get("description", None) if found else None

        print("Fetching descriptions for positives...")
        for i in positives:
            i["is_target_job_type"] = True
            i["description"] = find_description(i["jobid"])
            data.append(i)
        print("Fetching descriptions for negatives...")
        for i in negatives:
            i["is_target_job_type"] = True
            i["is_target_job_type"] = False
            i["description"] = find_description(i["jobid"])
            data.append(i)

        pd.DataFrame(data).to_csv(snapshot.path / fn, index=False)
        return snapshot.path / fn

    def report(self, snapshot=None):
        "Generate report using specified snapshot"
        predictions = jamie.snapshots.PredictionSnapshotCollection(
            self.cf["common.snapshots"]
        )
        snapshot = predictions[snapshot] if snapshot else predictions.latest()
        report = jamie.reports.Report(snapshot).create()
        print(success("Report successfully created"))
        print("   View it: jamie view-report {}".format(report.snapshot.name))

    def view_report(self, snapshot=None, port=8000):
        "Starts a local webserver to display reports"
        reports = jamie.snapshots.ReportSnapshotCollection(self.cf["common.snapshots"])
        snapshot = reports[snapshot] if snapshot else reports.latest()
        snapshot.view(port)

    def information_gain(
        self,
        training_snapshot=None,
        text_column="description",
        output_column="aggregate_tags",
    ):
        "Calculates information gain for text ngrams in training snapshot"
        training_snapshot = (
            jamie.snapshots.TrainingSnapshot(training_snapshot)
            if training_snapshot
            else jamie.snapshots.TrainingSnapshotCollection().latest()
        )
        return _information_gain(training_snapshot, text_column, output_column)

    def list_jobids(self):
        "List job ids from jobs database"
        db = connect_mongo(self.cf)
        for i in db[self.cf["db.jobs"]].find():
            print(i["jobid"])

    def distribution(self, kind):
        "Distribution of jobs in database: monthly or yearly"
        dist = collections.defaultdict(int)
        db = connect_mongo(self.cf)

        def _get_date(i):
            return (
                i.get("date", None) or i.get("placed_on", None) or i.get("closes", None)
            )

        for i in db[self.cf["db.jobs"]].find():
            date = _get_date(i)
            if date is None or isinstance(date, str):
                continue
            if kind == "monthly":
                dist["{:d}-{:02d}".format(date.year, date.month)] += 1
            else:
                dist[date.year] += 1
        data = pd.DataFrame(
            data=[(y, dist[y]) for y in sorted(dist)], columns=[kind[:-2], "frequency"]
        )
        print(data)
        print("Total:", data.frequency.sum())
