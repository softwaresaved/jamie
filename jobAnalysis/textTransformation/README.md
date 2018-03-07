# Text Transformation


Using the Natural Language Toolkit (NLTK) to transform text and use gensim to  transform the data into a TF-IDF representation. The next step is to build and train SVM model with sklearm and apply it on the entire dataset.

## Files

* [./include/configParser](./include/configParser) - Parsing config file, modify to give the possibility to parse a list

* [./include/vectorProcess.py](./include/vectorProcess.py) - Transform the bag of words in vectors and create the corpus file at the end

* [./include/dataStore.py](./include/dataStore.py) - To store data in file or in db

* [./include/logger.py](./include/logger.py) - A logger imported in different scripts. Output result in [./logs/](./logs/)

* [./include/textTransformation.py](./include/textTransformation.py) - Transform the raw text. 1. Remove URL - punctuation - stopword - number and lower case 2. Pos tag the words 3. Lemmatise the words 4. Stem the words 5. Output a bag of word

* [./include/tfidfTransformation.py](./include/tfidfTransformation.py) - Apply tfidf transformation on vectorised document

* [./include/update_nltk.py](./include/update_nltk.py) - Update the pickles files used by nltk and install them in the folder set up in config.ini. By default, the folder is in  [./nltk_files/](./nltk_files/)

* [./include/vectorProcess.py](./include/vectorProcess.py) - Vectorise a list of words using gensim and either create a new dictionary or load an existing one

* [./results](./results) - Folder where the dictionaries and corpus are saved after the vectorisation

* [./config.ini](./config.ini) - Contains all the variables such as input file, name of result directory,...

* [./jobstats.py](./jobstats.py) - Main script to call to launch the analysis. Need to configure option in [./config.ini](./config.ini) before doing it

* [./requirements.txt](./requirements.txt) - To install the requirements with `sudo pip install -r requirements.txt`


## Requirements

* Python 3.5
* `pip install -r requirements.txt`
* Installing Mongodb -- using docker
    * `sudo docker pull mongo:latest`
    * `sudo docker run -p 27017:27017 -v ~/data/mongodb/:/data/db --name mongod -d mongo`
* Access to the console inside the docker
    * `sudo docker exec -it mongod mongo`

* Using the [NLTK Python library](http://www.nltk.org/): This library requires some steps before being used.
    * Installing the corpus and data: The NLTK library works with different corpus and data that can be found [here](http://www.nltk.org/nltk_data/) and need to be locally installed.
        * Using the instructions [here](http://www.nltk.org/data.html) to install them system wide.
        * Using the [update_nlkt.py](update_nlkt.py) script to store the files under the folder specified  by the `nlkt_files` variable in [config.ini](config.ini). : `python3.5 update_nltk.py`
    * The list of needed corpus and data: Under the variable `list_pickles` in the [config.ini](config.ini)


## Use and reasons

The text containing the description of the job advert is stored inside

The process is divided in several steps:
1. Preparing the dataset
2. Train a model on a trained dataset that is obtained by extracting the corresponding tagged
documents from BOB (MySQL) and selecting the best model
3. Apply the model to the entire dataset


### 1. Cleaning Process and Feature extraction

<!-- TODO CHECK THE APPROPRIATE TERMINOLOGY  -->
Before applying the SVM, a feature extraction is needed and as important as the modelling and parametisation in SVM.
Several type of feature extractions exists, the Bag of word (BOW), where *a document is represented as a set of words, together with their associated frequency in the document*, and considering the text as string in which *each document is a sequence of words* (Aggarwal, 2012, p. 167).
The cleaning process is mainly to transform the text into a bag of word. The structure of sentences is removed and only a list of word is remained. All the punctuation is stripped and the words are all lowered.
Several additional cleaning are done at this stage, removing any email and URL address, removing any numbers and removing stop words (words that have high frequency in English but are removed to reduce the size of the bag of words.

This step is implemented in the [include/textClean.py](include/textClean.py) and use the [nltk](http://www.nltk.org/) library to transform the text into bag of words, as well as having the list of stop words in English.

The result is stored in the collection `txt_clean` under the key `txt_clean`. When the result is recorded in the collection, a key is updated in the original document in the collection `jobs`. The key is `txt_clean` and can be either `True` or `False`. It is `False` if the document does not contain a description or if it fails for any other reason.

Once the text is cleaned, the list is also transformed and the recorded under the same collection `txt_clean` but with the key `txt_trans`.
No additional key is added to the original document stored in the collection `jobs` and if the key `txt_clean` is set up to `True`, it assumed that the text is also transformed and recorded.

### 2. Text Transformation

As soon as the text is transformed into a bag of words, it is also possible to apply other transformation to reduce the size of the vector and some ambiguity.

Three separated processes are applied here, the [Part-of-speech Tagging (POS-tag)](https://en.wikipedia.org/wiki/Part-of-speech_tagging), the [Lemmatisation](https://en.wikipedia.org/wiki/Lemmatisation) and the [Stemming](https://en.wikipedia.org/wiki/Stemming).
They have different purposes but needs to be applied in this order as they rely on different types of information about the context that is destroyed when the text is transformed.
The guide used as a start for this work can be find [here](https://marcobonzanini.com/2015/03/02/mining-twitter-data-with-python-part-1/), it is a series of 7 articles describe some basic of text analysis using implemented in python.

#### 2.1. Part-of-speech Tagging (POS-tag)

From the [Wikipedia page](https://en.wikipedia.org/wiki/Part-of-speech_tagging) (retrieved on the 03/11/2016):

>In corpus linguistics, part-of-speech tagging (POS tagging or POST), also called grammatical tagging or word-category disambiguation, is the process of marking up a word in a text (corpus) as corresponding to a particular part of speech, based on both its definition and its context—i.e., its relationship with adjacent and related words in a phrase, sentence, or paragraph. A simplified form of this is commonly taught to school-age children, in the identification of words as nouns, verbs, adjectives, adverbs, etc.

The POS-tag consists into tagging a word to its grammatical category based on its position in the sentence. The POS-tag use algorithm and different dataset to decide which type of word it is.
The only purpose of the POS-tag for this text transformation is to give the contextual information to the lemmatiser.

To implement the POS-tag, the [NLKT POS-tagger](http://www.nltk.org/book/ch05.html) is used and return a tuple for each words, containing the word and the tag. The implementation is done within the [include/textProcess.py](include/textProcess.py)

#### 2.2. Lemmatisation

From the [Wikipedia page](https://en.wikipedia.org/wiki/Lemmatisation) (retrieved on the 03/11/2016):

> Lemmatisation (or lemmatization) in linguistics is the process of grouping together the inflected forms of a word so they can be analysed as a single item, identified by the word's lemma, or dictionary form.
> In computational linguistics, lemmatisation is the algorithmic process of determining the lemma of a word based on it's intended meaning. Unlike stemming, lemmatisation depends on correctly identifying the intended part of speech and meaning of a word in a sentence, as well as within the larger context surrounding that sentence, such as neighboring sentences or even an entire document.

The lemmatisation is to find the root of difference inflected words that are called lemma. The more common example is with the word "go". The lemmatiser will transform "go", "gone" and "went" to the root form: "go". The contextual information is needed to figure out if the word is a noun, a verb or an adjective.

The tagged words produced by the previous POS-tagging is used and output a lemmatized word (without the tag) using the WordNetLemmatizer algorithm from NLTK. An intermediary step is needed to convert the post-tag into the WordNet correspondence.

#### 2.3. Stemming

From the [Wikipedia page](https://en.wikipedia.org/wiki/Stemming) (retrieved on the 03/11/2016):

>In linguistic morphology and information retrieval, stemming is the process of reducing inflected (or sometimes derived) words to their word stem, base or root form—generally a written word form. The stem need not be identical to the morphological root of the word; it is usually sufficient that related words map to the same stem, even if this stem is not in itself a valid root.

This is the last transformation applied on the text. The root of the word is found and replace any variation (for instance gone, goes, to go) and reduce the dimensionality of the text.


The result of the conversion txt_clean -> POS-Tag -> Lemmatise -> stemmed is the recorded list `txt_trans` in the `txt_clean` collection.


### 3. Vectorised text

When the text is cleaned and transformation has been applied, it can be vectorised. It consists in receiving the bag of words and transforming it into a vector of id:frequency.
The implementation use the package gensim.

This script take a list of bag of word and map it to an id. It create two different output, a dictionary, containing the mapping and a corpus, containing the transformed text.
The corpus is a list of tuple, containing XXXXXXXXXXXXX
The dictionary is stored in a file (ending with `.dict`) and the corpus is stored in a file (ending with `.mm`).
However, the corpus grows with the number of documents and becomes not practical to use. Instead, the vectorised document is stored in the mongodb.

The results are stored into the key `vector_lem` for the vector created from the lemmatized a bag of word, `txt_lem`, and `vector_clean` for the vector created from the `txt_clean`.

The dictionary is still saved on the HD, as the same dictionary needs to be used over time.

### 4. TF-IDF Transformation

Not done yet because need to figure out the limitations first.


### Structure of the scheme stored`



## Sources and Documentation

Here listed the different sources used to implement and understand the text transformation and text analysis. It is not necessarily exhaustive. In case of you find some material that you are the original author, please contact the owner of the repository and we will solve it.

* [NLKT documentation](http://www.nltk.org/book/)
* [Regex used to remove URL found](http://stackoverflow.com/a/14081180/3193951): Used in [include/textClean.py](include/textClean.py)
* [Tutorial to implement text analysis in python using nltk](https://marcobonzanini.com/2015/03/02/mining-twitter-data-with-python-part-1/)
* [Another tutorial on how to use NLTK](http://textminingonline.com/dive-into-nltk-part-i-getting-started-with-nltk)
* [Tutorial to vectorize a text](https://radimrehurek.com/gensim/tut1.html)
* [Grid Search vs Random Search Article](http://www.jmlr.org/papers/v13/bergstra12a.html)
