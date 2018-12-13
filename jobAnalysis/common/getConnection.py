#!/usr/bin/env python
# encoding: utf-8

import pymongo
import pymysql

from common.configParser import configParserPerso as configParser
from common.logger import logger

logger = logger(name='getConnection', stream_level='DEBUG')


def connectMongo(config):
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

    # set up access credentials
    config_value = configParser()
    args_to_connect = list()
    args_to_connect.append(config.DB_NAME)
    # # MongoDB ACCESS # #
    try:
        DB_ACC_FILE = config.DB_ACCESS_FILE
        access_value = configParser()
        access_value.read(DB_ACC_FILE)
        args_to_connect.append(access_value['MongoDB'].get('db_username', None))
        args_to_connect.append(access_value['MongoDB'].get('DB_PASSWORD', None))

        args_to_connect.append(access_value['MongoDB'].get('DB_AUTH_DB', None))
        args_to_connect.append(access_value['MongoDB'].get('DB_AUTH_METHOD', None))
    except KeyError:
        pass

    # Get the information about the db and the collections
    # Create the instance that connect to the db storing the training set
    mongoDB = connectDB(*args_to_connect)
    return mongoDB


def connectMysql(config):
    """
    Connection to MySQL using MySQLdb module
    and return a cursor
    """
    def connectDB(self, *args, **kwargs):
        """
        """
        mdb = pymysql.connect(*args)
        return connector.cursor(mdb.cursors.DictCursor)

    # set up access credentials
    config_value = configParser()
    args_to_connect = list()
    args_to_connect.append(config.MYSQL_db_host)
    args_to_connect.append(config.MYSQL_db_name)
    args_to_connect.append(config.MYSQL_port)
    try:
        DB_ACC_FILE = config.DB_ACCESS_FILE
        access_value = configParser()
        access_value.read(DB_ACC_FILE)

        # # MYSQL ACCESS # #
        args_to_connect.append(access_value['MYSQL'].get('db_username', None))
        args_to_connect.append(access_value['MYSQL'].get('db_password', None))

    except KeyError:
        pass

    return connectDB(*args_to_connect)
