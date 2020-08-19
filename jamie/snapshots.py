# Get snapshots
import os
import json
import pickle
import http.server
import socketserver
import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import asdict
from .config import Config
from .types import JobPrediction
from .types import TrainingData
from .lib import bullet_text


class Snapshot:
    """Base class for a snapshot instance.

    Attributes
    ----------
    subpath : str
        This is set to the subfolder under the root snapshot
        folder in the derived classes.

    Parameters
    ----------
    instance : str
        Name of instance
    root : str
        Root path of snapshots (default : None)
    """

    subpath = ""
    _data = None
    _metadata = None

    def __init__(self, instance, root=None):
        self.instance = instance
        if root is None:
            cf = Config()
            self.root = Path(cf["common.snapshots"])
        else:
            self.root = Path(root)
        self.instance_location = self.root / self.subpath / self.instance

    def exists(self):
        "Returns whether instance exists"
        return self.instance_location.exists()

    def create(self):
        "Create instance location if it does not exist"
        if not self.exists():
            self.instance_location.mkdir(parents=True)
        return self

    @property
    def name(self):
        "Snapshot name"
        return self.instance

    @property
    def path(self):
        "Path to snapshot instance"
        return self.instance_location

    @property
    def data(self):
        "Data corresponding to the snapshot"
        pass

    def __str__(self):
        "String representation of snapshot"
        return (
            json.dumps(self.metadata, indent=2, sort_keys=True)
            if self.metadata
            else self.instance
        )

    @property
    def metadata(self):
        "Snapshot metadata"
        if self._metadata is None:
            metadata_file = self.instance_location / "metadata.json"
            with metadata_file.open() as fp:
                self._metadata = json.load(fp)
        return self._metadata


class SnapshotCollection:
    """Base class for collection of snapshots. Instances of derived class
    represent a collection of snapshots.

    Parameters
    ----------
    root : str, optional
        Root path of snapshots, uses default config to find if not specified
    startswith : str, optional
        If specified, restricts collection to instances that start with this string
    endswith : str, optional
        If specified, restricts collection to instances that end with this string
    """

    subpath = ""

    def __init__(self, root=None, startswith="", endswith=""):
        if root is None:
            cf = Config()
            self.root = Path(cf["common.snapshots"])
        else:
            self.root = Path(root)
        self.glob = startswith + "*" + endswith
        self.instances = [
            x.name for x in (self.root / self.subpath).glob(self.glob) if x.is_dir()
        ]

    @property
    def list(self):
        "List of instances in collection"
        return self.instances

    def keys(self):
        return self.list

    @property
    def is_empty(self):
        return self.instances == []

    def __contains__(self, key):
        "Returns whether instance *key* is in collection"
        return key in self.instances

    def __getitem__(self, key):
        "Returns snapshot instance if present in collection"
        if key in self.instances:
            return self.SnapshotClass(key, root=self.root)

    def __str__(self):
        "String representation of collection"
        return "\n".join(str(s) for s in self.list)

    def latest(self):
        "Returns latest instance in collection using lexicographical sorting"
        return self.SnapshotClass(sorted(self.instances)[-1], root=self.root)


class ReportSnapshot(Snapshot):
    "Represents a single report :class:`Snapshot`"
    subpath = "reports"  # NOQA

    @property
    def data(self):
        "Returns index.html of the report"
        if self._data is None:
            fn = self.instance_location / "index.html"
            self._data = fn.read_text()
        return self._data

    def view(self, port=8000):
        os.chdir(self.path)
        with socketserver.TCPServer(
            ("", port), http.server.SimpleHTTPRequestHandler
        ) as httpd:
            print(bullet_text("Viewing report at http://localhost:{}".format(port)))
            print("   Press Ctrl-C to stop the server")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.server_close()
                print()
                return


class TrainingSnapshot(Snapshot):
    "Represents a single training :class:`Snapshot`"
    subpath = "training"  # NOQA

    @property
    def data(self):
        "Returns DataFrame corresponding to training snapshot"
        if self._data is None:
            fn = self.instance_location / "training_set.csv"
            self._data = pd.read_csv(fn)
        return self._data

    def reliability(self):
        "Converts ratings into numerical scale for inter-rater reliability analysis"
        return TrainingData.reliability(self.data)


class ModelSnapshot(Snapshot):
    "Represents a single model :class:`Snapshot`"
    subpath = "models"  # NOQA

    @property
    def data(self):
        """Data corresponding to model snapshot. Returned as a dict:

        * model: The model object itself
        * scores: pd.DataFrame corresponding to best scores
        """
        if self._data is None:
            out = {}
            model_fn = self.instance_location / "model.pkl"
            scores_fn = self.instance_location / "scores.csv"
            if model_fn.exists():
                with model_fn.open("rb") as fp:
                    out["final_model"] = pickle.load(fp)
            model_fns = sorted(self.instance_location.glob("model_*.pkl"))
            out["indices"] = [fn.stem.replace("model_", "") for fn in model_fns]
            if scores_fn.exists():
                out["scores"] = pd.read_csv(scores_fn)
            self._data = out
        return self._data

    def model(self, index: str):
        "Returns model at index"
        with (self.instance_location / ("model_%s.pkl" % index)).open("rb") as fp:
            return pickle.load(fp)

    def features(self, index: str):
        "Returns features at index"
        with (self.instance_location / ("features_%s.pkl" % index)).open("rb") as fp:
            return pickle.load(fp)


class PredictionSnapshot(Snapshot):
    """Prediction Snapshot class"""

    subpath = "predictions"

    @property
    def data(self):
        "Returns data as dataframe"
        if self._data is None:
            self._predictions = []
            fn = self.instance_location / "predictions.jsonl"
            with fn.open() as fp:
                for pred in fp.readlines():
                    self._predictions.append(JobPrediction(json.loads(pred)))
            self._data = pd.DataFrame([asdict(x) for x in self._predictions])
        return self._data

    def partition_jobs(self, n_each_class=None, random_state=100):
        "Partition jobs into positive and negative class based on probability"
        positives, negatives = [], []
        if self._data is None:
            self._predictions = []
            fn = self.instance_location / "predictions.jsonl"
            with fn.open() as fp:
                for pred in fp.readlines():
                    prediction = JobPrediction(json.loads(pred))
                    if "PhD" in prediction.job_title:
                        continue
                    if prediction.probability_lower > 0.5:
                        positives.append(prediction.to_dict())
                    else:
                        negatives.append(prediction.to_dict())
        positives, negatives = np.array(positives), np.array(negatives)
        if n_each_class is None:
            return positives, negatives
        else:
            np.random.seed(random_state)
            sample_positives = np.random.choice(
                positives, size=n_each_class, replace=False
            )
            sample_negatives = np.random.choice(
                negatives, size=n_each_class, replace=False
            )
            return sample_positives, sample_negatives


class ReportSnapshotCollection(SnapshotCollection):
    "Training :class:`SnapshotCollection`, with subpath=reports"
    subpath = "reports"
    SnapshotClass = ReportSnapshot


class TrainingSnapshotCollection(SnapshotCollection):
    "Training :class:`SnapshotCollection`, with subpath=training"
    subpath = "training"
    SnapshotClass = TrainingSnapshot


class ModelSnapshotCollection(SnapshotCollection):
    "Model :class:`SnapshotCollection`, with subpath=models"
    subpath = "models"
    SnapshotClass = ModelSnapshot


class PredictionSnapshotCollection(SnapshotCollection):
    "Prediction :class:`SnapshotCollection`, with subpath=predictions"
    subpath = "predictions"
    SnapshotClass = PredictionSnapshot


def main(kind, instance=None):
    """CLI interface for snapshots.

    Parameters
    ----------
    kind : str
        Should be one of models/snapshots. Specifies which collection one wishes to show.
    instance : str, optional
        If specified, show a particular instance
    """
    c = Config()
    snapshot_path = Path(c["common.snapshots"])
    if not snapshot_path.exists():
        snapshot_path.mkdir()
    if kind == "models":
        if instance is None:
            return ModelSnapshotCollection(snapshot_path)
        else:
            return ModelSnapshotCollection(snapshot_path)[instance]
    elif kind == "training":
        if instance is None:
            return TrainingSnapshotCollection(snapshot_path)
        else:
            return TrainingSnapshotCollection(snapshot_path)[instance]
    elif kind == "predictions":
        if instance is None:
            return PredictionSnapshotCollection(snapshot_path)
        else:
            return PredictionSnapshotCollection(snapshot_path)[instance]
    elif kind == "reports":
        if instance is None:
            return ReportSnapshotCollection(snapshot_path)
        else:
            return ReportSnapshotCollection(snapshot_path)[instance]
    else:
        return "usage: jamie snapshots [training|models|predictions|reports]"
