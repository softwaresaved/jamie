#!/usr/bin/env python
# encoding: utf-8

"""
Transforming any raw text into a bag of words.
It gets a raw text composed of one sentence or an entire paragraph.
From there it splits the text into list of sentence.
Before splitting sentence into words it removes the emails and the
URL addresses.
Then it split every sentences into lists of words using regex and
remove some noises
"""

import string
import re
import unicodedata
import sys

from nltk import sent_tokenize
from nltk import word_tokenize
from nltk.corpus import stopwords

# from include.update_nltk import init_nltk


class TextClean:
    """
    Get a string as input of several sentence (or One), clean the text and return a list of words
    Break the text into several sentences
    Break the sentence into list of words
    Lower Case the words
    Remove stopwords, emails, URL, numbers, money symbol, punctuation, I
    Transform the 'll 's and remove them
    Flatten the list
    Return the list
    """

    def __init__(self, remove_stop=True, flat_list=True, **kwargs):
        """
        """
        self.remove_stop = remove_stop
        self.flat_list = flat_list
        # Allow to install the nltk files directly in the current folder
        # self.nltk_path = init_nltk(**kwargs)
        # if self.nltk_path:
        # data.path.append(self.nltk_path)
        self.stop_words = stopwords.words("english")
        # Use to remove the trailing punctuation in words that remain after tokenization
        self.REGEX_EMAIL = re.compile(
            (
                r"([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                r"{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                r"\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"
            )
        )
        self.REGEX_SPLIT = re.compile(r",|/|-|\s|'")
        # To remove trailing space with translate in python 3, need to apply
        # the following workaround in order to build the self.TABLE to use in the translate func()
        # Workaround can be found on the following
        # http://stackoverflow.com
        #   /questions/11066400
        #   /remove-punctuation-from-unicode-formatted-strings/21635971#21635971
        # Discussion about removing punctuation
        # http://stackoverflow.com/
        #   /questions/265960
        #   /best-way-to-strip-punctuation-from-a-string-in-python
        self.TABLE = dict.fromkeys(
            i
            for i in range(sys.maxunicode)
            if unicodedata.category(chr(i)).startswith("P")
        )
        # Remove the `#` form the dic to keep in in case of c#
        # FIXME Not having any impact yet because the word_tokenise is splitting c# in 'c', '#'
        del self.TABLE[35]
        # exceptions that have been encountered and are not dealt with all the automated options
        self.exceptions = set("``")

    @staticmethod
    def break_sentence(text):
        """
        Use nltk to tokenize sentences and return a list of sentences
        """
        return sent_tokenize(text)

    def remove_email(self, sentence):
        """
        Remove email address with the REGEX_EMAIL
        """
        return re.sub(self.REGEX_EMAIL, "", sentence)

    def break_word(self, sent):
        """
        Break sentence into list of word.
        Can use either the word_tokenise (preferred) or own
        simple splitting -- Also split words into several words when
        symbol in self.REGEX_SPLIT are encountered
        """
        return word_tokenize(re.sub(self.REGEX_SPLIT, " ", sent))
        # return re.split(self.REGEX_SPLIT, sent)

    @staticmethod
    def remove_punctuation(word):
        """
        Remove punctuation
        """
        if word not in string.punctuation:
            return word

    def remove_trailing_punctuation(self, word):
        """
        Get a list of words and remove the trailing punctuation on the words
        """
        return word.translate(self.TABLE)

    @staticmethod
    def lower_case(word):
        """
        Return lowered words
        """
        try:
            return word.lower()
        except AttributeError:
            return None

    @staticmethod
    def remove_number(word):
        """
        Remove all the numbers
        """

        def check_numeric(s):
            """
            Check if a string is a numeric, Return True if yes
            """
            try:
                float(s)
                return True
            except (ValueError, TypeError):
                return False

        if check_numeric(word) is False:
            return word

    @staticmethod
    def transform_apostrophe(word):
        """
        After tokenise the `'ll` `'s` `'nt` are considered as single word
        - `'s`: Removed as it is kept like that later and not being
                distinguished between the verb and the possessive
                #  TODO Check if the pos_tag_sentence() makes accurate distinction
        - `'ll`: transform into `will`
        - `'nt`: Is transformed into `n't` by the token_sentence().
                    Convert this `n't` into `not`
        """
        if word.startswith("'"):
            if word == "'s":
                pass
            elif word == "'ll":
                return "will"
            else:
                return word
        else:
            if word == "n't":
                return "not"
            else:
                return word

    @staticmethod
    def remove_I(word):
        """
        Remove the I that is not removed from the stop words list
        """
        if word != "i":
            return word

    @staticmethod
    def remove_currency(word):
        """
        Remove all the money symbol and the money associated if they are attached
        """
        # http://stackoverflow.com/questions/25978771/what-is-regex-for-currency-symbol
        try:
            for ch in [word[0], word[-1]]:
                if unicodedata.category(ch) == "Sc":
                    # return an empty word instead of None
                    # and get removed in the remove_empty_words()
                    return None
            return word
        except IndexError:  # In case the word is empty, return an empty word
            return None
        except TypeError:
            return None

    @staticmethod
    def remove_empty_words(word):
        """
        Sometime empty words are kept in the sentence ['', 'word']
        probably due to break_word()
        :params: :word: str()
        :return: word: str()
        """
        if word != "":
            return word

    def remove_exceptions(self, word):
        """
        Remove the word if equal to any exception set in
        the set self.exceptions()
        :params: word:str()
        :return: word: str()
        """
        if word not in self.exceptions:
            return word

    def remove_stop_word(self, word):
        """
        Remove the word if in stop word list
        """
        if word not in self.stop_words:
            return True

    def remove_stop_sent(self, sent):
        """
        Remove the stop words from a sentence
        and return the cleaned sentence
        :params: sent: list of str() to clean
        :return: a list of str() w/o stop words
        """
        return [word for word in sent if self.remove_stop_word(word)]

    @staticmethod
    def flattening_list(text):
        """
        Flattening the list of list into a flat list
        :params: list() of sentence (list() of words)
        :return: 2 list() of words cleaned and transformed
        """
        return [word for sentence in text for word in sentence]

    @staticmethod
    def remove_url(word):
        """
        Remove the word if it's start with http or www
        to do approximate cleaning of URL
        :params word str(): word to check
        :return word str(): return words if not matching the
        condition
        """
        try:
            if not word.startswith(("www", "http")):
                return word
        except AttributeError:
            return None

    def clean_word(self, word):
        """
        Apply a the cleaning written in this class for the sentence
        :params: words: str() to parse and clean
        :return: words: str() of cleaned words
        """
        word = self.transform_apostrophe(word)
        word = self.remove_trailing_punctuation(word)
        word = self.remove_number(word)
        word = self.lower_case(word)
        # word = self.remove_I(word)
        word = self.remove_currency(word)
        word = self.remove_exceptions(word)
        word = self.remove_url(word)
        # word = self.remove_empty_words(word)
        return word

    def clean_sentence(self, input_list):
        """
        Apply a the cleaning written in this class for the sentence
        :params: input_list: list of str() to parse and clean
        :return: output_list: list of str() of cleaned words
        """
        output_list = list()
        input_list = self.remove_email(input_list)
        for word in self.break_word(input_list):
            word = self.clean_word(word)
            if word:
                output_list.append(word)
        return output_list

    def clean_text(self, text):
        """
        wrapper around the function to process the txt passed into the
        argument. The txt can also be transformed
        :params: :text: raw txt composed of str()
        :returns::txt_cleaned: list of str() containing the cleaned words
        """
        txt_cleaned = list()
        for sent in self.break_sentence(text):
            sent_cleaned = self.clean_sentence(sent)
            # Remove the stop words from the sent_cleaned
            if self.remove_stop:
                sent_cleaned = self.remove_stop_sent(sent_cleaned)
            txt_cleaned.append(sent_cleaned)
        if self.flat_list is True:
            return self.flattening_list(txt_cleaned)
        return txt_cleaned

    def clean_stop(self, text):
        """
        wrapper around the function to process the txt and remove the
        stop words. The txt needs to be a list of list of str()
        :params: txt: list() of list() of str()
        :return: txt_cleaned of list() of list() of str()
        """
        txt_cleaned = list()

        for sent in text:
            sent_cleaned = self.remove_stop_sent(sent)
            txt_cleaned.append(sent_cleaned)

        return txt_cleaned
