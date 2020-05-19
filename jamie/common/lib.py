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
