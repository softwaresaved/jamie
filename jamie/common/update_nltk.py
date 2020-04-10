#!/usr/bin/env python
# encoding: utf-8

"""
Using nltk requires to download separately the pickle files.
This script check if the required module are available and updated
If not launch then it installs or updates them.
Also, set up the OS environment variable to a local folder to ensure
that the file are installed there instead of the default installation
folder. This to keep all the needed file into the same folder.
This nltk modules are needed for the include/topicTranformation.py
"""


# TODO: Even if files are present, redownload everything while before skipping it
# if found up-to-date files
# No need of init_env_var() but keep it becauce may be needed to fix this bug with the
# update

import os
import errno
from include.configParser import ConfigParserPerso as configParser


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def get_config():
    """ """
    config_value = configParser()
    config_value.read('./config.ini')
    return config_value


def init_env_var(var, value):
    """ Init an environment variable """
    os.environ[var.upper()] = str(value)


def import_nltk(folder=None):
    """
    Change the os variable and then return the module
    If the module is imported before the change of the env_var, the change
    of the var is not applied
    """
    import nltk as nltk
    # Create it global but not sure is needed
    global nltk
    # insert the custom path into the list of folder that nltk can search in
    if folder is not None:
        nltk.data.path.insert(0, folder)


def dl_pickles(l, folder=None):
    """
    Download the pickle file name input as list or string
    """
    print('Starting to download the modules')
    if isinstance(l, list):
        for element in l:
            if folder is not None:
                nltk.download(element, download_dir=folder)
            else:
                nltk.download(element)

    elif isinstance(l, str):
        if folder is not None:
            nltk.download(l, download_dir=folder)
        else:
            nltk.download(l)
    else:
        raise('Not a list or a string, Abort, it is a {}'.format(type(l)))


def update_nltk(nltk_files=None, list_pickles=None):
    """
    Download the required files
    """
    config_value = get_config()
    if nltk_files is None:
        nltk_files = config_value['nltk'].get('nltk_files'.lower(), None)
        print(nltk_files)
    if list_pickles is None:
        list_pickles = config_value['nltk'].get('list_pickles'.lower(), None)
        print(list_pickles)
    init_env_var('nltk_data', nltk_files)
    make_sure_path_exists(nltk_files)
    import_nltk(nltk_files)
    dl_pickles(list_pickles, nltk_files)


def init_nltk(**kwargs):
    """
    Receive the config value content
    and return the nltk_files after
    update if needed
    """
    # Get the nltk_file folder if set up in the config.ini
    # Used in the init of text_process() to add it in the
    # nltk module. Search inside that folder for nltk files
    nltk_files = kwargs['nltk'].get('NLTK_FILES', None)

    # Get the list of files to get if update is trure
    nltk_list = kwargs['nltk'].getlist('NLTK_LIST', None)

    # Get the value to know if processing the update of the nltk file
    nltk_update = kwargs['nltk'].get('NLTK_UPDATE', False)
    if nltk_update == 'True':
        update_nltk(nltk_files, nltk_list)

    # return the location of nltk files to be used in the cleaning function
    return nltk_files


if __name__ == '__main__':
    update_nltk()
