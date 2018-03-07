#!/usr/bin/env python
# encoding: utf-8


"""
Transform bag of words into vector using corpora func() from Gensim.
The class returns the vector only and to store the dictionary.
It is also possible to store it into a corpus and to store the corpus on the hard drive
"""


import os
import errno
import itertools
from gensim import corpora
# from include.benchmark import timeit
# from include.logger import logger

# logger = logger(name='vectorProcess', stream_level='DEBUG')


class vectorProcess(object):
    """
    This class counts and transforms the bag of words into a
    vector. It indexes all the words in a separate dictionary
    and then maps the corresponding words into the vector.
    The non-present words are ignored, the vector only contains
    the words that are present.
    The dictionary is updated every time a list of new documents is parsed
    The init() method does the following:
        1. Get the dictionary of the corpus or init an empty one
    The run() method does the following:
        1. Received a list of words (bag_of_words)
        2. Update the corpus dictionary
        3. Create the vector of the present words (id: freq)
        4. Output the vector as a list
        5. Optional (save the corpus and the dictionary on the hard-drive)
    """
    def __init__(self, dict_name=None, corpus_name=None, result_dir='./results/', do_corpus=False):
        """
        Dictionary encapsulates the mapping between normalized words
        and their integer ids.
        """
        self.result_dir = self._set_up_result_folder(result_dir)

        # Create the proper name for the dictionary. Does not include the complete path
        self.dict_name = self._getname(dict_name, 'dictionary')

        # To save the dictionary
        self.target = os.path.join(self.result_dir, self.dict_name)
        self.dictionary = self._load_obj(self.dict_name, result_dir, 'dictionary')

        # Setting self.do_corpus to know if record corpus information or not
        # Used in the function run() to setup on False or True (False by default)
        self.do_corpus = do_corpus
        if self.do_corpus:
            # Create the proper name for the corpus. Does not include the complete path
            self.corpus_name = self._getname(corpus_name, 'corpus')
            self.corpus = self._load_obj(self.corpusname, result_dir, 'corpus')

    @staticmethod
    def _set_up_result_folder(path):
        """
        Check for the existence of the result directory and if not existing, create a new one
        :params: path - str() to the path of the folder
        :return: path - str() with the folder name
        """
        if os.path.exists(path):
            return path
        try:
            os.makedirs(path)
            return path
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise OSError('Not possible to create a folder to store the result -- \
                               Check the value of result_dir')

    def _getname(self, obj_name, type_obj):
        """
        Create the proper name by adding the right extension.
        Create a default object if none is parsed.
        :params:
            :obj_name: str() of dictionary filename or a corpora.dictionary.Dictionary obj()
            :type_obj: str() either 'dictionary' or 'corpus' to return the right object
        :return: return_name: str() of the name + the right extension
        """
        if obj_name:
            # return the name given + the proper extension
            if type_obj == 'dictionary':
                extension = '.dict'
            elif type_obj == 'corpus':
                extension = '.mm'
            else:
                raise TypeError('''Not a proper type of object to instanciate \
                                Need to be either dictionary or corpus but received:
                                {}'''.format(type_obj))
            return obj_name + extension
        return self._getname(type_obj, type_obj)

    @staticmethod
    def _load_obj(obj_name, directory, type_obj):
        """
        To load the dictionary if it exists or create a new ones if not
        :params:
            :obj_name: str() of dictionary filename
            :directory: str() of folders name where dictionary is going to be stored
            :type_obj: str() either 'dictionary' or 'corpus' to return the right object
        :returns:
            :corporate.dictionary.Dictionary: Dict obj() from gensim if 'type_obj' == 'dictionary
            :corpus: list() to be used as a corpus to store the vectorise data (in form of tuple())
                        if type_obj == 'corpus'
        """

        obj_filename = os.path.join(directory, obj_name)
        try:
            if os.path.isfile(obj_filename):
                # logger.debug('Loading pre-existing {} from filename'.format(type_obj))
                if type_obj == 'dictionary':
                    return corpora.dictionary.Dictionary.load(obj_filename)
                elif type_obj == 'corpus':
                    return list()
            else:
                # logger.debug('{0} not found -- Create a new {0}'.format(type_obj))
                if type_obj == 'dictionary':
                    return corpora.dictionary.Dictionary(obj_filename)
                elif type_obj == 'corpus':
                    return list()
        except TypeError:
            # logger.debug('No {0} passed -- Create a new {0}'.format(type_obj))
            if type_obj == 'dictionary':
                return corpora.dictionary.Dictionary()
            elif type_obj == 'corpus':
                return list()

    @staticmethod
    def flattening_list(input_list):
        """
        Receive a list and return an flatten list
        using itertool
        :params: input_list list(): input_list to be flatten
        :return list(): flatten list
        """
        return itertools.chain.from_iterable(input_list)

    @staticmethod
    def check_bag_of_words(bag_of_words):
        """
        Check the bag of words to ensure that it is a list
        of UTF-8 encoded string
        """
        # TODO: Double pass the list for checking and apply the transformation -- Need to do on one pass
        try:
            return [elt.encode('utf-8') for elt in bag_of_words]
        except AttributeError:
            return list()

    def update_dict(self, bag_of_words):
        """
        Update dictionary from a collection of documents.
        Each document is a list of tokens = tokenized and normalized
        strings (either utf8 or unicode).
        """
        # Need to be parsed in a list of list of words
        self.dictionary.add_documents([bag_of_words])

    def token2id(self, bag_of_words):
        """
        Use the generated corpus dictionary to return a vector of token_id
        """
        # Need to be parsed in a list of list of words
        return self.dictionary.doc2bow(bag_of_words)

    def get_vector(self, bag_of_words, do_corpus=False, update_dict=True):
        """
        Run the process
        :params:
            bag_of_words: list() of str() or list()
        """
        if isinstance(bag_of_words[0], list):
            bag_of_words = self.flattening_list(bag_of_words)
        bag_of_words = self.check_bag_of_words(bag_of_words)
        if update_dict is True:
            self.update_dict(bag_of_words)
        vector = self.token2id(bag_of_words)
        if self.do_corpus is True and do_corpus is True:
            self.corpus.append(vector)
        return vector

    # def _save_obj(self, type_obj, filename=None):
    #     """
    #     Common method to record either the dictionary or the corpus on the HD
    #     :params:
    #         :type_obj: str() with the type of obj to be recorded. Can be either 'dictionary' or 'corpus'
    #         :filename: str() to append to the self.dict_name to create a specific dictionary
    #                    for the specific instance
    #     """
    #     if filename is None:
    #         return type_obj
    #     try:
    #         return filename.encode('utf-8')
    #     except Exception:  # TODO Specify exception
    #         logger.debug('Not a proper filename, record as {}'.format(type_obj))
    #         return self._save_obj(type_obj, filename=type_obj)

    def save_dict(self):
        """
        Save the corpus dictionary on the HD
        """
        self.dictionary.save(self.target)

    def save_corpus(self, filename=None):
        """
        Save the `self.corpus_dict` on the HD
        """
        corpora.MmCorpus.serialize(self.target)


def main():

    output_folder = './results/'

    vector_clean_process = vectorProcess(dict_name='clean', result_dir=output_folder)
    vector_trans_process = vectorProcess(dict_name='trans', result_dir=output_folder)
    vector_clean_process.run(['f', 'x', 'z'])
    print(vector_clean_process.dictionary)
    vector_clean_process.save_dict()
    vector_trans_process.save_dict()


if __name__ == "__main__":
    main()
