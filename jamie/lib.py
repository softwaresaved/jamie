# Common functions used throughout JAMIE
import os
import sys
import errno
import datetime
import pymongo

OK = " \033[92m✔\033[0m "
FAIL = " \033[31m×\033[0m "


def bold(text):
    "Return text in bold"
    return "\033[1m{}\033[0m".format(text)


def status_text(status, text):
    "Returns status text"
    return OK + bold(text) if status else FAIL + bold(text)


def connect_mongo(cfg):
    "Returns connection to MongoDB given configuration"

    if "JAMIE_MONGO_URI" in os.environ:
        client = pymongo.MongoClient(os.environ["JAMIE_MONGO_URI"])
    else:
        client = pymongo.MongoClient()

    return client[cfg["db.name"]]


def setup_messages(msgs):
    "Pretty prints setup messages"
    return "\n".join(status_text(s, t) for s, t in msgs)


def fail(msg, exitcode=1):
    "Fail with message and exitcode (default: 1)"
    print(status_text(False, msg))
    sys.exit(exitcode)


def check_nltk_download(*datasets):
    "Check NLTK download for datasets"
    import nltk

    return all(nltk.download(dataset, quiet=True) for dataset in datasets)


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
