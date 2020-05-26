# Get snapshots
import json
import pickle
import pandas as pd
from pathlib import Path
from .config import Config
from box import Box

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

    def data(self):
        "Data corresponding to the snapshot"
        pass

    def __str__(self):
        "String representation of snapshot"
        m = self.metadata()
        return json.dumps(m, indent=2, sort_keys=True) if m else self.instance

    def metadata(self):
        "Snapshot metadata"
        metadata_file = self.instance_location / 'metadata.json'
        if metadata_file.exists():
            with metadata_file.open() as fp:
                return json.load(fp)
        else:
            return None

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

    def list(self):
        "Returns list of instances in collection"
        return self.instances

    def __contains__(self, key):
        "Returns whether instance *key* is in collection"
        return key in self.instances

    def __str__(self):
        "String representation of collection"
        return '\n'.join(str(s) for s in self.list())

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

    def data(self):
        "Returns DataFrame corresponding to training snapshot"
        fn = self.instance_location / 'training_set.csv'
        if fn.exists():
            return pd.read_csv(fn)
        else:
            return None

class ModelSnapshot(Snapshot):
    "Represents a single model :class:`Snapshot`"
    subpath = "models"  # NOQA

    def data(self):
        """Returns Box corresponding to model snapshot. Box has

        * model: The model object itself
        * scores: pd.DataFrame corresponding to best scores
        """
        out = {}
        model_fn = self.instance_location / 'model.pkl'
        scores_fn = self.instance_location / 'scores.csv'
        if model_fn.exists():
            with model_fn.open('rb') as fp:
                out['model'] = pickle.load(fp)
        if scores_fn.exists():
            out['scores'] = pd.read_csv(scores_fn)
        return Box(out)


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

