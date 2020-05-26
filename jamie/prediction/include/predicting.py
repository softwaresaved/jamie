#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))


import pandas as pd

from common.logger import logger
from common.getConnection import connectMongo

__author__  = "Olivier Philippe"

"""
Take a feature pipeline and a model and predict new entry in the mongodb
Return the prediction as 1-0 and the probability and update the document with
the prediction
"""


def main():
    pass


if __name__ == "__main__":
    main()
