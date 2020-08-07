from pathlib import Path
import pytoml as toml
from .common.lib import arrow_table

DEFAULTS = {
    "common.snapshots": Path("snapshots"),
    "scrape.folder": Path("input"),
    "common.nltk-files": Path("nltk-files"),
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
    cf = DEFAULTS
    cache = Path("~/.cache/jamie").expanduser()
    paths = ["common.snapshots", "scrape.folder", "common.nltk-files"]

    def __init__(
        self, filename=Path("~/.config/jamie/config.toml").expanduser(), who="jamie"
    ):
        self.who = who
        self.filename = filename
        self.exists = Path(filename).exists()
        if filename.exists():
            with filename.open() as fp:
                _cf = toml.load(fp)
            for k in _cf:
                if not isinstance(_cf[k], dict):
                    raise ValueError(
                        "Incorrect configuration file format in %s" % self.filename
                    )
                else:
                    for y in _cf[k]:
                        key = "%s.%s" % (k, y)
                        if key in self.paths:
                            self.cf[key] = Path(_cf[k][y]).expanduser()
                        else:
                            self.cf[key] = _cf[k][y]
        if not self.cache.exists():
            self.cache.mkdir(parents=True)

    def __contains__(self, s):
        return s in self.cf

    def __str__(self):
        return arrow_table(self.cf.items())

    def get(self, s, default=None):
        if s in self.cf:
            return self.cf[s]
        else:
            return default

    def set(self, s, val):
        if s in self.paths:
            if not isinstance(val, Path):
                raise ValueError("%s accepts Path keys")
        try:
            root, child = s.split(".")
        except:
            raise ValueError("Indentation level not two levels (abc.xyz)")
        cf = {}
        for k in self.cf:
            r, c = k.split(".")
            if r not in cf:
                cf[r] = {}
            if k in self.paths:
                cf[r][c] = str(self.cf[k])
            else:
                cf[r][c] = self.cf[k]
        if root not in cf:
            cf[root] = {}
        if s in self.paths:
            cf[root][child] = str(val)
        else:
            cf[root][child] = val
        with self.filename.open("w") as fp:
            toml.dump(cf, fp)

    def save(self, folder, name="config.toml"):
        cf = {}
        for k in self.cf:
            r, c = k.split(".")
            if r not in cf:
                cf[r] = {}
            if k in self.paths:
                cf[r][c] = str(self.cf[k])
            else:
                cf[r][c] = self.cf[k]

        with (folder / name).open("w") as fp:
            toml.dump(cf, fp)

    def as_dict(self):
        cf = self.cf.copy()
        for k in cf:
            if k in self.paths:
                cf[k] = str(cf[k])
        return cf

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
