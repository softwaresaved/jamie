import json
from pathlib import Path
from collections import ChainMap
from .lib import arrow_table

DEFAULTS = {
    "common.snapshots": "snapshots",
    "scrape.folder": "input",
    "common.nltk-files": "nltk-files",
    "scrape.njobs": 10000,
    "db.name": "jobsDB",
    "db.tags": "tags",
    "db.jobs": "jobs",
    "db.prediction": "prediction",
    "db.mysql-host": "127.0.0.1",
    "db.mysql-port": None,
    "db.mysql-name": "classify",
    "model.k-fold": 5,
}


class Config:
    cache = Path("~/.cache/jamie").expanduser()
    paths = ["common.snapshots", "scrape.folder", "common.nltk-files"]

    def __init__(
        self, filename=Path("~/.config/jamie/config.json").expanduser(), who="jamie"
    ):
        self.who = who
        self.filename = filename
        self.exists = Path(filename).exists()
        _cf = {}
        if filename.exists():
            with filename.open() as fp:
                _cf = json.load(fp)
        # Find keys successively in specified config and then defaults
        self.cf = ChainMap(_cf, DEFAULTS)
        if not self.cache.exists():
            self.cache.mkdir(parents=True)

    def ensure_config_location_exists(self):
        if not self.filename.parent.exists():
            self.filename.parent.mkdir(parents=True)

    def __contains__(self, s):
        return s in self.cf

    def __str__(self):
        return arrow_table(self.cf.items())

    def get(self, s, default=None):
        if s in self.paths:
            return Path(self.cf[s]) if s in self.cf else default
        return self.cf.get(s, default)

    def set(self, s, val):
        try:
            root, child = s.split(".")
        except ValueError:
            raise ValueError("All configuration items are two levels (abc.xyz)")
        self.ensure_config_location_exists()
        if isinstance(val, Path):
            val = str(Path)
        # New value in front of ChainMap same value later on
        cf = self.cf.new_child({s: val})
        with self.filename.open("w") as fp:
            json.dump(dict(cf), fp, sort_keys=True, indent=2)

    def as_dict(self):
        return dict(self.cf)

    def save(self, folder, name="config.json"):
        with (folder / name).open("w") as fp:
            json.dump(self.as_dict(), fp, sort_keys=True, indent=2)

    def __getitem__(self, key):
        return self.cf[key]


def configurator(field=None, new_value=None):
    c = Config()

    if field is None:
        print(
            "jamie: configuration file %s -- %s\n"
            "  config               List current configuration\n"
            "  config <name>        Read value of configuration <name>\n"
            "  config <name> <val>  Set configuration <name> to <val>\n\n"
            "Current configuration:"
            % ("(not present, using defaults)" if not c.exists else "", c.filename)
        )
        print(c)
    elif field is not None and new_value is None:
        return str(c.get(field))
    elif field is not None and new_value is not None:
        c.set(field, new_value)
    else:
        return "config: Can only set value for a known field"
