# Features

from .default import RSEFeatures

def select_features(f):
    if f == 'rse' or f == 'default':
        return RSEFeatures
    return None

