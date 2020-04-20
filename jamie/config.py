from pathlib import Path
import pytoml as toml

DEFAULTS = {
    'scrape.folder': 'input',
    'common.nltk-files': './nltk-files/',
    'scrape.njobs': 10000,
    'db.name': 'jobsDB',
    'db.tags': 'tags',
    'db.prediction': 'prediction',
    'db.mysql-host': '127.0.0.1',
    'db.mysql-port': None,
    'db.mysql-name': 'classify',
    'model.oversampling': False,
    'model.k-fold': 5
}

class Config:
    cf = DEFAULTS
    cache = Path("~/.cache/jamie").expanduser()

    def __init__(self, filename=Path("~/.config/jamie.toml").expanduser(), who="jamie"):
        self.who = who
        self.filename = filename
        if filename.exists():
            with filename.open() as fp:
                _cf = toml.load(fp)
            for k in _cf:
                if not isinstance(_cf[k], dict):
                    raise ValueError("Incorrect configuration file format in %s" % self.filename)
                else:
                    for y in _cf[k]:
                        key = "%s.%s" % (k, y)
                        if key in self.paths:
                            self.cf[key] = Path(_cf[k][y]).expanduser()
                        else:
                            self.cf[key] = _cf[k][y]
        if not self.cache.exists():
            self.cache.mkdir(parents=True)

    def has(self, s):
        return s in self.cf

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
            root, child = s.split('.')
        except:
            raise ValueError("Indentation level not two levels (abc.xyz)")
        cf = {}
        for k in self.cf:
            r, c = k.split('.')
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
        with self.filename.open('w') as fp:
            toml.dump(cf, fp)

    def __getitem__(self, key):
        return self.cf[key]

def main(args):
    c = Config()
    if len(args) == 0:
        print("syntax: jamie config <configname>")
    elif len(args) == 1:
        print(str(c.get(args[0])))
    else:
        c.set(args[0], args[1])
