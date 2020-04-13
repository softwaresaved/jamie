#!/usr/bin/env python
# encoding: utf-8

"""
Script to deal with the mongodb using pymongo
"""

class dbOperation:
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """

    def connect(self, *args, **kwargs):
        """
        """

    def build_dict(self, *args):
        """
        Receive a key: Tuple() and create a formatted search query for pymongo
        """
        return {args[0]: {'${}'.format(args[1][0]): args[1][1]}}


    def specific_search(self, coll, type_search, *args, **kwargs):
        """
        Search in mongodb the query passed in arguments
        :params:
            *coll: MongoDB collection object to connect to
            *type_search: type of result to obtain -- Possible value [find, count]
            *kwargs: Key value to search: Key is the key in mongodb and value is a tuple
                ** the tuple is composed of the operation (exists, in, nin, ...) and a value to search
        :return: a mongoObject from the research
        """
        search = dict()
        for key in kwargs:
            search.update(build_dict(key, kwargs[key]))
        print(search)


def main():
    specific_search('coll', 'count', TypeRole=('exists', 'true'), InvalidCode=('nin', ['1', '2', '3']))


if __name__ == "__main__":
    main()
