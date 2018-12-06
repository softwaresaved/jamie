#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Config file to return the appropriate config file
"""
import importlib



def Config(config_file_name):
    """
    :params:
        config_file_name str(): name of the config file to import
    :return:
        Return the config file as stated in the init
    """
    file_name = '{}.py'.format(config_file_name)
    # file_name = config_file_name
    imported_config = importlib.import_module(file_name)
    return imported_config.Config
    # config = Config()
    # return config

