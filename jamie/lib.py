# Common functions used throughout JAMIE
import os
import errno
import datetime
import pymongo
from .logger import logger


def connect_mongo(cfg):
    "Returns connection to MongoDB given configuration"

    _logger = logger(name="database", stream_level="DEBUG")
    if "JAMIE_MONGO_URI" in os.environ:
        client = pymongo.MongoClient(os.environ["JAMIE_MONGO_URI"])
    else:
        client = pymongo.MongoClient()
        _logger.info("Connection to the database without password and authentication")

    return client[cfg["db.name"]]


def isodate():
    return datetime.datetime.now().date().isoformat()


def isotime_snapshot():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def table(tuples, align, sep=""):
    tuples = list(tuples)
    ncol = len(tuples[0])  # assume all tuples of same length
    sep = " " + sep + " "
    if len(align) != ncol:
        raise ValueError("align and ncol have to be equal")

    def maxlen(xs):
        return max(len(str(x)) for x in xs)

    def select_col(n):
        return [t[n] for t in tuples]

    def justify(s, align_type, length):
        length += 2
        if align_type == "l":
            return str(s).ljust(length)
        elif align_type == "r":
            return str(s).rjust(length)
        else:
            return str(s).center(length)

    maxlens = [maxlen(select_col(n)) for n in range(ncol)]
    return "\n".join(
        [
            sep.join(justify(i[k], align[k], maxlens[k]) for k in range(ncol))
            for i in tuples
        ]
    )


def arrow_table(tuples):
    return table(tuples, align="rl", sep="⯈")
