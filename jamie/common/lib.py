# Common functions used throughout JAMIE
import os
import git
import errno
import datetime


def gitversion():
    repo = git.Repo(__file__, search_parent_directories=True)
    return repo.git.describe()


def isodate():
    return datetime.datetime.now().date().isoformat()


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
