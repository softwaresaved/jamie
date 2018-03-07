#!/usr/bin/env python
# encoding: utf-8


import pymongo
try:
    from include.logger import logger
except ModuleNotFoundError:
    from logger import logger
try:
    from include.configParser import ConfigParserPerso as configParser
except ModuleNotFoundError:
    from configParser import ConfigParserPerso as configParser

# ## GLOBAL VARIABLES  ###
# # To set up the variable on prod or dev for config file and level of debugging in the
# # stream_level
RUNNING = 'dev'

if RUNNING == 'dev':
    CONFIG_FILE = '../config_dev.ini'
    DEBUGGING='DEBUG'
elif RUNNING == 'prod':
    CONFIG_FILE = 'config.ini'
    DEBUGGING='INFO'

logger = logger(name='Training_classifier', stream_level=DEBUGGING)


class collectData(object):
    """
    Interface with the mongo database to collect the data and
    return a generator that contain the id, the tags and the data.
    It use the collection 'tags', where the different tags and associated jobid
    are stored, as well as either txt_clean or txt_feature collection, where the
    feature data are stored
    It supposes a data structure scheme created during the textTransformation
    process for the features' collection and the datastructure of tags, created
    during the dbPreparation
    The object returned is generic generator that help to interface with the
    trainingInstance
    """

    def __init__(self, *args):
        """
        Receiving the arguments needed to connect to the database and pass them
        into the get_connection() to create a pymongo obj()
        :params:
            :db_name: args[0] name of the database (Required)
            :user: args[1] str() of the user (Optional)
            :passw: args[2] str() of the password (Optional)
            :db_auth: args[3] str() of the type of authentication used (Optiona)
            :db_mech: args[4] str() of the mechanism of auth (Optional)
        """
        self.db = self.get_connection(*args)

    def get_connection(self, *args):
        """
        Parse the argument to Pymongo Client
        and return a collection object to connect to the db
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

    def return_collection(self, collection='tags'):
        """
        Return the collection name where the tags are
        """
        return self.db[collection]

    def building_pipeline(self, collection, *args, **kwargs):
        """
        Build a pipeline for the aggregator in mongodb.
        1. match: Return the documents that have either SoftwareJob set to Yes or to None in
            the db.tags collection
        2. lookup: do inner join from the jobid keys in the db.collection to find which of the
            jobid are present in the collection given by args[0]
        3. Unwind: the result under the `data` keys to have access to all the keys/values
        4. second_match: only match the results that satisfied the k:v given with **kwargs
        5. project: return only the jobid, the tag and the data

        :params:
            :collection str(): which database need to be queried
            :args: which keys need to be returned. If not args specified, return the entire document
            :kwargs: the keys and values to match which type of data needed to be returned. If none, return all the
            data associated for each keys

        :return: list() pipeline to be parsed into the aggregate function
        """
        match = {'$match': {'$or': [{'SoftwareJob': 'Yes'}, {'SoftwareJob': 'None'}]}}
        lookup = {'$lookup': {'from': collection, 'localField': 'jobid', 'foreignField': 'jobid', 'as': 'data'}}
        unwind = {'$unwind': '$data'}
        field_to_return = {'jobid': 1, 'SoftwareJob': 1}
        if args:
            added_field_to_return = dict(('data.{}'.format(k), 1) for k in args)
            field_to_return.update(added_field_to_return)

        project = {'$project': field_to_return}
        if kwargs:
            second_match = {'$match': {'$and': [{'data.{}'.format(k): v} for k, v in kwargs.items() if v is not None]}}
            # project = {'$project': {'jobid': 1, 'SoftwareJob': 1, 'data.data': 1}}
            return [match, lookup, unwind, second_match, project]
        return [match, lookup, unwind, project]


    def get_documents(self, collection, *args, **kwargs):
        """
        Get a collection object than build the pipeline and return the id, tag and associated vector
        :params:
            :collection: mongDB.collection() collection where txt data are stored
            :args: which keys need to be returned. If not args specified, return the entire document
            :**kwargs: string of the fields that needs to be parsed. The different possibilities are
                :input_field str(): Which field it is from the job advert
                :operation str(): which operation that has been applied on the data to generate it
                :input_data str(): which data have been used. If the collection used is db.txt_clean, this
                field is ommited.
        :return:
            :document[jobid]: str() of the jobid
            :document['SoftwareJob']: str() of the tag associated to the jobid,
             either 'Yes' or 'None'
            :document[0][type_vector]: list() of list() of tuple()
             that contain the vector of the document
        """
        db = self.return_collection()
        pipeline = self.building_pipeline(collection, *args, **kwargs)
        for document in db.aggregate(pipeline):
            try:
                yield document['jobid'], document['SoftwareJob'], document['data']
            except IndexError:  # Happen when the vector is empty because not processed in the vector db
                yield document['jobid'], document['SoftwareJob'], None
            except KeyError:
                raise


def main():
    """
    For test purpose only
    """

    # ### CONNECTION TO DB ### #

    # set up access credentials
    # config_value = configParser().read_config(CONFIG_FILE)
    config_value = configParser()
    config_value.read(CONFIG_FILE)

    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)
    access_value = configParser()
    access_value.read(DB_ACC_FILE)
    # # MongoDB ACCESS # #
    mongoDB_USER = access_value['MongoDB'].get('db_username'.lower(), None)
    mongoDB_PASS = access_value['MongoDB'].get('DB_PASSWORD'.lower(), None)
    mongoDB_AUTH_DB = access_value['MongoDB'].get('DB_AUTH_DB'.lower(), None)
    mongoDB_AUTH_METH = access_value['MongoDB'].get('DB_AUTH_METHOD'.lower(), None)

    # # MYSQL ACCESS # #

    # Get the information about the db and the collections
    mongoDB_NAME = config_value['MongoDB'].get('DB_NAME'.lower(), None)

    # connect to the mongoDB
    mongoDB = collectData(mongoDB_NAME, mongoDB_USER,
                          mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    n = 0
    for doc in mongoDB.get_documents('txt_feature',
                                     operation="lemmatise",
                                     input_field="JobTitle",
                                     input_data="clean"):
        n+=1
        print(doc)
    print(n)
    for doc in mongoDB.db['txt_feature'].find({}):
        print(doc)


if __name__ == "__main__":
    main()
