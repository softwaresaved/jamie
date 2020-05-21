# Get snapshots
import sys
from pathlib import Path
from .config import Config
from tabulate import tabulate

class Snapshot:
    subpath = ''
    glob = '*'

    def __init__(self, root):
        self.root = Path(root)
        self.instances = list((self.root / self.subpath).rglob(self.glob))
        self.root_instances = ['/'.join(k for k in s.parent.parts
                               if k not in ['snapshots', self.subpath])
                               for s in self.instances]
        self.instance_map = {k: v for k, v in zip(self.root_instances, self.instances)}

    def list(self):
        return self.root_instances

    def __getitem__(self, key):
        return self.instance_map.get(key, None)

    def __contains__(self, key):
        return key in self.instance_map

    def __str__(self):
        return '\n'.join(str(s) for s in self.list())

    def table(self):
        return tabulate(self.instance_map.items())

    def most_recent(self):
        return sorted(self.root_instances)[0]


class TrainingSnapshot(Snapshot):
    subpath = 'training'
    glob = '*.csv'


class ModelSnapshot(Snapshot):
    subpath = 'models'
    glob = '*.pkl'


def main(arg):
    c = Config()
    snapshot_path = Path(c['common.snapshots'])
    if not snapshot_path.exists():
        snapshot_path.mkdir()
    if arg == 'models':
        return str(ModelSnapshot(snapshot_path))
    elif arg == 'training':
        return str(TrainingSnapshot(snapshot_path))
    else:
        return "usage: jamie list-snapshots [models|training]"

