#!/usr/bin/env python
# encoding: utf-8

import pymongo
import pytoml as toml


from ..logger import logger

logger = logger(name="getConnection", stream_level="DEBUG")


def read_toml(fn):
    with open(fn) as fp:
        return toml.load(fp)


def connectMongo(cfg):
    """
    """

    def connectDB(*args):
        """
        Parse the argument to Pymongo Client
        and return a db object
        """
        db = args[0]
        c = pymongo.MongoClient()
        try:
            user, passwd, db_auth, db_mech = args
            confirmation = c[db].authenticate(
                user, passwd, source=db_auth, mechanism=db_mech
            )
            logger.info("Authenticated: {}".format(confirmation))
        except (IndexError, ValueError, TypeError):
            logger.info(
                "Connection to the database without password and authentication"
            )
        return c[db]

    args_to_connect = [cfg["db.name"]]
    # # MongoDB ACCESS #
    if "db.access" in cfg:
        access_value = read_toml(cfg["db.access"])
        args_to_connect += [
            access_value["MongoDB"].get("db_username", None),
            access_value["MongoDB"].get("DB_PASSWORD", None),
            access_value["MongoDB"].get("DB_AUTH_DB", None),
            access_value["MongoDB"].get("DB_AUTH_METHOD", None),
        ]

    # Get the information about the db and the collections
    # Create the instance that connect to the db storing the training set
    mongoDB = connectDB(*args_to_connect)
    return mongoDB
