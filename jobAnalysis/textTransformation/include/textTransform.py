#!/usr/bin/env python
# encoding: utf-8

"""
A class which transfrom a text by applying POS-TAG - lemmatize and stemmization.
The text which is received needs to be a list of sentence. Each sentence is also a list
containing the bag of words.
"""


from nltk import pos_tag, data
from nltk import sent_tokenize
from nltk.corpus import wordnet
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer

from include.update_nltk import init_nltk
from include.textClean import textClean

# from include.benchmark import timeit
from include.logger import logger
logger = logger(name='textTAG_LEM_STEM', stream_level='DEBUG')


class textTransform(textClean):
    """
    Receive a string input and transform it with the NLTK library
    1. Tag the words with a POS_TAG
    2. Lemmatize the word using the tagged tuple
    3. Apply a stemmer
    4. Return a list of stemmed words
    """
    def __init__(self, **kwargs):
        """
        Init the stop word list, stemmer and lemmatizer from the nltk library
        :params: **kwargs: location of the nltk file and if an update is needed
        """
        # Import to get access to remove_stop_words() and getting access to breaking_sentence
        # Add the path to the nltk module to search the files within that folder
        textClean.__init__(self, **kwargs)
        # Allow to install the nltk files directly in the current folder
        self.nltk_path = init_nltk(**kwargs)
        if self.nltk_path:
            data.path.append(self.nltk_path)
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()

    # @timeit
    def pos_tag_sentence(self, sentence):
        """
        Get a sentence as a list and return a list of tuple with the
        information on the word. Used for the stemmization later
        """
        return pos_tag(sentence)

    # @timeit
    def lem_word(self, sentence):
        """
        Get a tuple of word and lemmatize word
        """
        def convert_tag(tag):
            """
            Need to convert the POS_TAG into the recognized form for the
            lemmatizer
            """
            if tag.startswith('J'):
                return wordnet.ADJ
            elif tag.startswith('V'):
                return wordnet.VERB
            elif tag.startswith('N'):
                return wordnet.NOUN
            elif tag.startswith('R'):
                return wordnet.ADV
            elif tag.startswith('s'):
                return wordnet.ADJ_SAT
            else:
                return None

        list_file = list()
        for word in sentence:
            pos_tag = convert_tag(word[1])
            if pos_tag:
                lem = self.lemmatizer.lemmatize(word[0], pos=pos_tag)
            else:
                lem = self.lemmatizer.lemmatize(word[0])
            list_file.append(lem)
        return list_file

    # @timeit
    def stem_word(self, sentence):
        """
        Stemming is the process of reducing a word into its root form.
        The root form is not necessarily a word by itself, but it can be
        used to generate words by concatenating the right suffix.
        source: http://marcobonzanini.com/2015/01/26/stemming-lemmatisation-and-pos-tagging-with-python-and-nltk/
        """
        return [self.stemmer.stem(word) for word in sentence]

    def transform_sentence(self, sentence):
        """
        Apply all the transformation on the sentence and return the cleaned one
        :params: sentence: list() of str
        :return: setence: list() of str transformed
        """
        sentence = self.pos_tag_sentence(sentence)
        sentence = [word for word in sentence if self.remove_stop_word(word[0])]
        sentence = self.lem_word(sentence)
        sentence = self.stem_word(sentence)
        return sentence

    def transform_text(self, text):
        """
        Run method to get a text str and return the fully transformed
        string back
        :params:
            :text: list() containing  a sentence of str()
        :return: output_txt: list of string (transformed with the method
                                  from the class)
        """
        # To check if I pass a list of broken sentence or full text
        if not isinstance(text[0], list):
            text = sent_tokenize(text)
        output_txt = list()
        for sentence in text:
            output_txt.append(self.transform_sentence(sentence))
        return output_txt


def main():
    pass


if __name__ == '__main__':
    main()
