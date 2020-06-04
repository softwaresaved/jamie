# Get snapshots
import json
import datetime
import pickle
import pandas as pd
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from .config import Config
from box import Box

Date = datetime.date

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
            self.root = Path(cf['common.snapshots'])
        else:
            self.root = Path(root)
        self.instance_location = self.root / self.subpath / self.instance

    def exists(self):
        "Returns whether instance exists"
        return self.instance_location.exists()

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
        m = self.metadata()
        return json.dumps(m, indent=2, sort_keys=True) if m else self.instance

    @property
    def metadata(self):
        "Snapshot metadata"
        if self._metadata is None:
            metadata_file = self.instance_location / 'metadata.json'
            with metadata_file.open() as fp:
                self._metadata = json.load(fp)
        return self._metadata

class SnapshotCollection:
    """Base class for collection of snapshots. Instances of derived class
    represent a collection of snapshots.

    Parameters
    ----------
    root : str
        Root path of snapshots
    startswith : str, optional
        If specified, restricts collection to instances that start with this string
    endswith : str, optional
        If specified, restricts collection to instances that end with this string
    """

    subpath = ''

    def __init__(self, root, startswith="", endswith=""):
        self.root = Path(root)
        self.glob = startswith + "*" + endswith
        self.instances = [x.name for x in (self.root / self.subpath).glob(self.glob) if x.is_dir()]

    @property
    def list(self):
        "List of instances in collection"
        return self.instances

    def __contains__(self, key):
        "Returns whether instance *key* is in collection"
        return key in self.instances

    def __str__(self):
        "String representation of collection"
        return '\n'.join(str(s) for s in self.list)

    def most_recent(self):
        "Returns most recent instance in collection using lexicographical sorting"
        return sorted(self.instances)[0]


class TrainingSnapshotCollection(SnapshotCollection):
    "Training :class:`SnapshotCollection`, with subpath=training"
    subpath = 'training'

    def __getitem__(self, key):
        if key in self.instances:
            return TrainingSnapshot(key, self.root)

class ModelSnapshotCollection(SnapshotCollection):
    "Model :class:`SnapshotCollection`, with subpath=models"
    subpath = 'models'

    def __getitem__(self, key):
        if key in self.instances:
            return ModelSnapshot(key, self.root)

class TrainingSnapshot(Snapshot):
    "Represents a single training :class:`Snapshot`"
    subpath = "training"  # NOQA

    @property
    def data(self):
        "Returns DataFrame corresponding to training snapshot"
        if self._data is None:
            fn = self.instance_location / 'training_set.csv'
            self._data = pd.read_csv(fn)
        return self._data

class ModelSnapshot(Snapshot):
    "Represents a single model :class:`Snapshot`"
    subpath = "models"  # NOQA

    @property
    def data(self):
        """Data corresponding to model snapshot. Returned in a Box:

        * model: The model object itself
        * scores: pd.DataFrame corresponding to best scores
        """
        if self._data is None:
            out = {}
            model_fn = self.instance_location / 'model.pkl'
            scores_fn = self.instance_location / 'scores.csv'
            if model_fn.exists():
                with model_fn.open('rb') as fp:
                    out['final_model'] = pickle.load(fp)
            model_fns = sorted(self.instance_location.glob('model_*.pkl'))
            out['indices'] = [fn.stem.replace("model_", "") for fn in model_fns]
            if scores_fn.exists():
                out['scores'] = pd.read_csv(scores_fn)
            self._data = out
        return Box(self._data)

    def model(self, index: str):
        "Returns model at index"
        with (self.instance_location / ("model_%s.pkl" % index)).open('rb') as fp:
            return pickle.load(fp)

    def features(self, index: str):
        "Returns features at index"
        with (self.instance_location / ("features_%s.pkl" % index)).open('rb') as fp:
            return pickle.load(fp)


class Contract(Enum):
    "Contract type: Fixed Term or Permanent"
    FixedTerm = auto()
    Permanent = auto()

@dataclass
class JobPrediction:
    """Represents prediction for a single job

    Attributes
    ----------
    jobid : str
        JobID from jobs.ac.uk
    snapshot : str
        Model snapshot used for prediction
    closes : Date
        Close date for job
    contract : Contract
        Contract type
    department : str
        Department of the academic institution that
        the job is associated with
    employer : str
        Job employer
    posted : Date
        Date job was posted
    salary_min : Optional[int]
        Minimum salary associated with the job. Sometimes
        jobs have a range of salaries depending on the experience
        of the applicant.
    salary_max : Optional[int]
        Maximum salary associated with the job. Sometimes
        jobs have a range of salaries depending on the experience
        of the applicant.
    salary_median : Optional[int]
        Median salary associated with the job.
    probability : float
        Probability that the job is classified in the positive class
    probability_lower : float
        Lower confidence interval of the probability
    probability_upper : float
        Upper confidence interval of the probability

    Parameters
    ----------
    prediction : dict
        Dictionary representing a single prediction from the JSONL file
        generated by :class:`Predict`
    """
    jobid: str
    snapshot: str
    contract: str
    department: str
    employer: str
    hours: List[str]
    job_title: str
    posted: Date
    location: str
    salary_max: Optional[int] = None
    salary_min: Optional[int] = None
    salary_median: Optional[int] = None
    probability: float
    probability_lower: float
    probability_upper: float

    def __init__(self, prediction):
        self.jobid = prediction['jobid']
        self.snapshot = prediction['snapshot']
        self.contract = Contract.Permanent if prediction['contract'] == 'Permanent' \
            else Contract.FixedTerm
        self.employer = prediction['employer']
        self.hours = prediction['hours']
        self.job_title = prediction['job_title']
        self.location = prediction['location']
        if 'salary_max' in prediction:
            self.salary_max = prediction['salary_max']
        if 'salary_min' in prediction:
            self.salary_max = prediction['salary_min']
        if 'salary_median' in prediction:
            self.salary_median = prediction['salary_median']
        for p in ['probability', 'lower_ci', 'upper_ci']:
            if not 0 <= prediction[p] <= 1:
                raise ValueError("Tried reading invalid {}={}.".format(
                    p, prediction[p]))
        self.probability = prediction['probability']
        self.probability_lower = prediction['lower_ci']
        self.probability_upper = prediction['upper_ci']
        self.posted = datetime.datetime.fromisoformat(
            prediction['json']['datePosted']).date()

class PredictionSnapshot(Snapshot):
    """Prediction Snapshot class"""
    subpath = "predictions"

    @property
    def data(self):
        "Returns data as dataframe"
        pass

class PredictionSnapshotCollection(SnapshotCollection):
    "Prediction :class:`SnapshotCollection`, with subpath=predictions"
    subpath = "predictions"

    def __getitem__(self, key):
        if key in self.instances:
            return ModelSnapshot(key, self.root)


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
    snapshot_path = Path(c['common.snapshots'])
    if not snapshot_path.exists():
        snapshot_path.mkdir()
    if kind == 'models':
        if instance is None:
            return ModelSnapshotCollection(snapshot_path)
        else:
            return ModelSnapshotCollection(snapshot_path)[instance]
    elif kind == 'training':
        if instance is None:
            return TrainingSnapshotCollection(snapshot_path)
        else:
            return TrainingSnapshotCollection(snapshot_path)[instance]
    else:
        return "usage: jamie snapshots [models|training]"
