#!/usr/bin/env python
# encoding: utf-8

import pymongo
from common.configParser import configParserPerso as configParser
from common.logger import logger

logger = logger(name='getConnection', stream_level='DEBUG')


def connectDB(config_file):
    """
    """
    # ### CONNECTION TO DB ### #

    # set up access credentials
    config_value = configParser()
    config_value.read(config_file)

    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)
    access_value = configParser()
    access_value.read(DB_ACC_FILE)
    # # MongoDB ACCESS # #
    mongoDB_USER = access_value['MongoDB'].get('db_username'.lower(), None)
    mongoDB_PASS = access_value['MongoDB'].get('DB_PASSWORD'.lower(), None)
    mongoDB_AUTH_DB = access_value['MongoDB'].get('DB_AUTH_DB'.lower(), None)
    mongoDB_AUTH_METH = access_value['MongoDB'].get('DB_AUTH_METHOD'.lower(), None)

    # Get the information about the db and the collections
    mongoDB_NAME = config_value['MongoDB'].get('DB_NAME'.lower(), None)
    # Create the instance that connect to the db storing the training set
    mongoDB = connectMongo(mongoDB_NAME, mongoDB_USER,
                           mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    return mongoDB


def connectMongo(*args):
    """
    Parse the argument to Pymongo Client
    and return a db object
    """
    db = args[0]
    c = pymongo.MongoClient()
    try:
        user = args[1]
        passw = args[2]
        db_auth = args[3]
        db_mech = args[4]
        confirmation = c[db].authenticate(user,
                                            passw,
                                            source=db_auth,
                                            mechanism=db_mech)
        logger.info('Authenticated: {}'.format(confirmation))
    except (IndexError, ValueError, TypeError):
        logger.info('Connection to the database without password and authentication')
    return c[db]
