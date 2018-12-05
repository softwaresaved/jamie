#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Config file to return the appropriate config file
"""

class config:

    def __init__(self, config_file_name):
        """
        :params:
            config_file_name str(): name of the config file to import
        """
        self.config_file_name = './{}.py'.format(config_file_name)


    def __call__(self):
        """
        Return the config file as stated in the init
        """
        return __import__(self.config_file_name)

