#!/usr/bin/env python
# encoding: utf-8


"""
Take a dictionary and corpus of vectorised document and apply tfidf on it
return it as vector as well as store it into a db
"""


from gensim import corpora, models

try:
    from include.configParser import ConfigParserPerso as configParser
except ImportError:
    from configParser import ConfigParserPerso as configParser
try:
    from include.dataStore import dataStore
except ImportError:
    from dataStore import dataStore
try:
    from include.logger import logger
except ImportError:
    from logger import logger

logger = logger(name='topicTransformation', stream_level='DEBUG')


class topicTransformation(object):
    """
    Transform a corpus composed of vectorised documents, into
    a reduced dimension vectors
    Can use different transformation algo
    Returns:
    * A Tfidf vector
        * saved into the db
        * a list()
    * The transformed corpus
        * Stored into a file
    """

    def __init__(self, output_folder, db, filename):
        """
        :params: output_folder: folder where information is stored
        :params: filename: Name use to get the corpus file, the dictionary file
                    and the db collection from it. All filenames are supposed
                    to follow the structure of txt_filename.dic txt_filename.mm
                    vector_filename (collection)
        :params: db: MongoDB object to store the tf-idf
        """
        self.output_folder = output_folder
        self.db = db
        self.filename = filename

    def load_dict(self):
        """
        Load the dictionary
        """
        self.dictionary = corpora.Dictionary.load('{}{}.dict'.format(self.output_folder, self.filename))

    def load_corpus(self):
        """
        Load a corpus from a file
        """
        self.corpus = corpora.MmCorpus('{}{}.mm'.format(self.output_folder, self.filename))

    def train_tfidf(self):
        """
        Transform into a Tfidf
        """
        self.tfidf = models.TfidfModel(self.corpus)  # step 1 -- initialize a model

    def apply_tfidf(self, vector):
        """
        Apply the trained tfidf model on vector
        Parameters:
        *vector: list of index and frequency
        Return:
        * tfidf_vector: the vector with the tfidf transformation
        """
        self.corpus_tfidf = self.tfidf[self.corpus]  # step 2 -- use the model to transform vectors
        return self.tfidf[vector]

    def save_model(self, corpus, algo):
        """
        Save the entire vectors tranformed with tfidf into a file
        Parameters
        *corpus: the trained corpus to save
        * algo: the name of the algo used (tfidf)
        Returns:
        * file stored in self.output_folder, with the self.filename.algo name
        """
        corpora.MmCorpus.serialize('{}{}.{}'.format(self.output_folder,
                                                    self.filename, algo), corpus)

    def run(self):
        """ """
        logger.info('Load the dictionary: {}'.format(self.filename))
        self.load_dict()
        logger.info('Load the corpus: {}'.format(self.filename))
        self.load_corpus()
        logger.info('Train the tfidf model: {}'.format(self.filename))
        self.train_tfidf()
        dbname = 'vector_{}'.format(self.filename)
        logger.info('Apply the tfidf model on the vectors: {}'.format(self.filename))
        for vector in self.db.get_record('find', dbname):
            tfidf_vector = self.apply_tfidf(vector[dbname])
            self.db.get_record('update', 'tfidf_{}'.format(self.filename),
                               search={'jobid': vector['jobid']},
                               update={'vector': tfidf_vector})
        logger.info('Save the model under: {}{}.tfidf'.format(self.output_folder, self.filename))
        self.save_model(self.corpus_tfidf, 'tfidf')


def main():
    """ """
    config_value = configParser().read_config('./config.ini')
    output_folder = config_value.get('output_folder', None)

    # set up connection to the db
    db = dataStore(**config_value)
    logger.info('Run the topic transformation for clean txt')
    topic_transformation = topicTransformation(output_folder, db, 'clean')
    topic_transformation.run()
    logger.info('Run the topic transformation for lem txt')
    topic_transformation = topicTransformation(output_folder, db, 'lem')
    topic_transformation.run()

if __name__ == '__main__':
    main()
