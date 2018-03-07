#!/usr/bin/env python
# encoding: utf-8

"""
    This script connect to a database and then expose method to insert update
    or return documents from a MongoDB
"""
from pymongo import MongoClient
from pymongo.collection import Collection as MongoCol
from pymongo import errors as MongoError


class dataStore(object):
    """
        connect to a database and return method to insert/update/find/random/replace
        any document.
        If a document is returned, it is returned as dict()
    """
    def __init__(self, *args, **kwargs):
        """
            - dbhost: In case the db is not on the same machine, otherwise
                      default value is localhost
            - dbport: Default port for mongo is 27017 - can be change
            - dbuser: need to secure the db default user is SSI
            - dbpass: Need to secure the db access (vm visible from outside)
            - dbname: Name of the database used
        """
        host = kwargs.get('dbhost', 'localhost')
        port = int(kwargs.get('dbport', 27017))
        self.dbname = kwargs.get('dbname', None)
        self.dbuser = kwargs.get('dbuser', None)
        self.dbpass = kwargs.get('dbpass', None)
        if self.dbname is not None:
            self.db = self.return_db(self.dbname, host, port)
        else:
            raise TypeError('Not a proper dbname, check the value')
        # if self.colname is not None:
        #     self.coll = self.return_col()
        # else:
        #     raise TypeError('need to have a collection name')

    def return_db(self, dbname, host, port):
        """ Return a db object with host - port - dbuser - dbpass set up in the
            init if no option given
        """
        # client = MongoClient(self.host, self.port, self.dbuser, self.dbpass)
        client = MongoClient(host, port)
        return client[dbname]

    # def return_col(self):
    #     """ Return a db object with the host, port, user, pass
    #         dbname and colname
    #     """
    #     # Check if it is a string. If yes, just pass that string into
    #     # db.object from pymongo and return it
    #     if isinstance(self.colname, str):
    #         self.coll = self.db[self.colname]
    #     else:
    #         raise TypeError('Need to parse a string')

    def get_record(self, method, collection=None, search=None, update=None,
                   rand_num=None, upsert=True, set_option='$set'):
        """ """
        def remove_key(dict_, key_to_remove):
            """
                Remove a key from the dictionary if needed
            """
            try:
                del dict_[str(key_to_remove)]
            except (KeyError, TypeError):
                pass
            return dict_

        # TODO insert the check after a try/except for not impacting performance
        def check_db(collection):
            """
                Offer the possibility to input a db object or to build it
                with the name as collection name and settings from the __init__
            """
            # MongoCol is a collection object from pymongo
            if isinstance(collection, MongoCol):
                return collection
            # If receive a str(), send it to the func() return_db which going to build
            # the object using the properties of the class
            elif isinstance(collection, str()):
                return self.return_db(collection)
            else:
                raise TypeError('Not a collection object or a string to build a db')

        # TODO insert the check after a try/except for not impacting performance
        # db = check_db(collection)
        if search is None:
            search = {}
        if method == 'update':
            update = remove_key(update, '_id')
            return self.db[collection].find_one_and_update(search, {set_option: update}, upsert=upsert)
        elif method == 'replace':
            update = remove_key(update, '_id')
            return self.db[collection].find_one_and_replace(search, update, upsert=upsert)
        elif method == 'remove':
            return self.db[collection].find_one_and_delete(search)
        elif method == 'insert':
            return self.db[collection].insert_one(update)
        elif method == 'random':
            return self.db[collection].find(search, skip=int(rand_num), limit=-1)
        elif method == 'find_one':
            return self.db[collection].find_one(search)


def main():
    db = dataStore(dbname='test1', colname='text')
    db.get_record('insert', 'text', update={'test': 10})
    db.get_record('insert', 'raw', update={'test': 911})

if __name__ == '__main__':
    main()
