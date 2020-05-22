# Get snapshots
import json
import pickle
import pandas as pd
from pathlib import Path
from .config import Config
from box import Box

class Snapshot:
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
        return self.instance_location.exists()

    def data(self):
        pass

    def metadata(self):
        metadata_file = self.instance_location / 'metadata.json'
        if metadata_file.exists():
            with metadata_file.open() as fp:
                return json.load(fp)
        else:
            return None

class SnapshotCollection:
    subpath = ''

    def __init__(self, root, startswith="", endswith=""):
        self.root = Path(root)
        self.glob = startswith + "*" + endswith
        self.instances = [x.stem for x in (self.root / self.subpath).glob(self.glob) if x.is_dir()]

    def list(self):
        return self.instances

    def __contains__(self, key):
        return key in self.instances

    def __str__(self):
        return '\n'.join(str(s) for s in self.list())

    def most_recent(self):
        return sorted(self.instances)[0]


class TrainingSnapshotCollection(SnapshotCollection):
    subpath = 'training'

    def __getitem__(self, key):
        if key in self.instances:
            return TrainingSnapshot(key, self.root)

class ModelSnapshotCollection(SnapshotCollection):
    subpath = 'models'

    def __getitem__(self, key):
        if key in self.instances:
            return ModelSnapshot(key, self.root)

def TrainingSnapshot(Snapshot):
    subpath = "training"  # NOQA

    def data(self):
        fn = self.instance_location / 'training_set.csv'
        if fn.exists():
            return pd.read_csv(fn)
        else:
            return None

def ModelSnapshot(Snapshot):
    subpath = "models"  # NOQA

    def data(self):
        out = {}
        model_fn = self.instance_location / 'model.pkl'
        scores_fn = self.instance_location / 'scores.csv'
        if model_fn.exists():
            with model_fn.open('rb') as fp:
                out['model'] = pickle.load(fp)
        if scores_fn.exists():
            out['scores'] = pd.read_csv(scores_fn)
        return Box(out)


def main(arg):
    c = Config()
    snapshot_path = Path(c['common.snapshots'])
    if not snapshot_path.exists():
        snapshot_path.mkdir()
    if arg == 'models':
        return ModelSnapshotCollection(snapshot_path)
    elif arg == 'training':
        return TrainingSnapshotCollection(snapshot_path)
    else:
        return "usage: jamie snapshots [models|training]"

