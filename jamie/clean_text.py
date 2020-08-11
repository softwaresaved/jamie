"""
Text cleaning
=============

This module transforms a raw text into a bag of words after cleaning. The following
operations are performed:

* Get a string as one or more sentences, clean the text and return a list
  of words
* Break the text into several sentences
* Break the sentence into list of words
* Lowercase the words
* Remove stopwords, emails, URL, numbers, money symbols, punctuation, I
* Transform the 'll 's and remove them
"""

import re
import unicodedata
import sys
from contextlib import suppress
import nltk

REGEX_EMAIL = re.compile(
    (
        r"([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
        r"{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
        r"\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"
    )
)
REGEX_SPLIT = re.compile(r",|/|-|\s|'")

# To remove trailing space with translate in Python 3, need to apply the
# following workaround in order to build the TABLE to use in the translate
# func()

# Workaround can be found on the following http://stackoverflow.com/questions/11066400
# Discussion about removing punctuation http://stackoverflow.com/questions/265960

TABLE = dict.fromkeys(
    i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith("P")
)

# Exceptions that have been encountered and are not dealt with all the
# automated options
EXCEPTIONS = set("``")


def _remove_email(sentence):
    return re.sub(REGEX_EMAIL, "", sentence)


def _break_word(sent):
    return nltk.word_tokenize(re.sub(REGEX_SPLIT, " ", sent))


def _remove_number(word):
    return word if not _is_numeric(word) else None


def _remove_exceptions(word):
    return word if word not in EXCEPTIONS else None


def _remove_trailing_punctuation(word):
    return word.translate(TABLE)


def _lower_case(word):
    return word.lower() if isinstance(word, str) else None


def _is_numeric(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _transform_apostrophe(word):
    """
    After tokenise the `'ll` `'s` `'nt` are considered as single word
    - `'s`: Removed as it is kept like that later and not being
            distinguished between the verb and the possessive
            #  TODO Check if the pos_tag_sentence() makes accurate distinction
    - `'ll`: transform into `will`
    - `'nt`: Is transformed into `n't` by the token_sentence().
                Convert this `n't` into `not`
    """
    return {"'s": None, "'ll": "will", "n't": "not"}.get(word, word)


def _remove_currency(word):
    # http://stackoverflow.com/questions/25978771/what-is-regex-for-currency-symbol
    with suppress(IndexError, TypeError):
        for ch in [word[0], word[-1]]:
            if unicodedata.category(ch) == "Sc":
                return None
        return word


def _remove_stop_sent(sent):
    "Remove stopwords from sentence"
    return [word for word in sent if word not in nltk.corpus.stopwords.words("english")]


def _remove_url(word):
    with suppress(AttributeError):
        if not word.startswith(("www", "http")):
            return word


def _clean_word(word):
    for transform in [
        _transform_apostrophe,
        _remove_trailing_punctuation,
        _remove_number,
        _lower_case,
        _remove_currency,
        _remove_exceptions,
        _remove_url,
    ]:
        word = transform(word)
    return word


def _clean_sentence(input_list):
    return filter(  # Remove None from list
        None, map(_clean_word, _break_word(_remove_email(input_list)))
    )


def clean_text(text, remove_stop=True, flat_list=True):
    "Main text cleaning method"
    sentences = map(_clean_sentence, nltk.sent_tokenize(text))
    if remove_stop:
        sentences = map(_remove_stop_sent, sentences)
    return sum(sentences, []) if flat_list else list(sentences)
