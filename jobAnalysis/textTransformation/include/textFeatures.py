#!/usr/bin/env python
# encoding: utf-8


"""
A collection of function to extract features from a text.
It suppose the text has been transformed into a list of sentence which also
are a list of word (str())
"""


from nltk import ngrams
from nltk import sent_tokenize
# from include.logger import logger

# logger = logger(name='ngrams', stream_level='DEBUG')


class ngramCreator:
    """
    A class to extract ngrams from a list of strings
    """

    def __init__(self, ngram=2, joiner='_'):
        """
        :params:
            :ngram: int() of size of the ngram, default is 2
            :joiner: char() to join the ngram together. If set up on False, return
                        tuple instead of string
        """
        self.ngram = ngram
        self.joiner = joiner

    def check_type_sentence(self, text):
        """
        Check if it is a list of broken sentences or a full text in str()
        And return a token list if it is a str() or return w/o transformation
        if it is a list
        :params:
            text list() or str(): Input txt to check if list() or str()
        :return:
            text list(): return the tokenized text (list)
        """
        if isinstance(text, str):
            text = sent_tokenize(text)
        return text

    def run(self, text):
        """
        Use the ngrams from nltk and join every words to create only one
        :params:
            :text: list of str() or complete str() text to break into ngrams
        :return: output_text: list of the ngrams as either str() if joiner is used
                                or tuple if joiner is False
        """
        text = self.check_type_sentence(text)
        output_text = list()
        for sentence in text:
            if self.joiner:
                output_text.append([self.joiner.join(n) for n in ngrams(sentence, self.ngram)])
            else:
                output_text.append([n for n in ngrams(sentence, self.ngrams)])
        return output_text


def main():
    # text = ['Bonjour', 'monsieur', 'le', 'president']
    text = [['Bonjour', 'monsieur', 'le', 'president'], ['c', 'est', 'un', 'plaisir']]
    # text = 'Bonjour monsieur le president'
    ngram_ = ngramCreator()
    print(ngram_.run(text))
    pass


if __name__ == "__main__":
    main()
