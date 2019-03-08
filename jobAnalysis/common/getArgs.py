#!/usr/bin/env python
# encoding: utf-8


"""
Wrapper for getting arguments to be used in __main__ of different scripts in the project
"""

import argparse
import config.config as config

# List of valid arguments for the parser in each scripts whe argparse is called
valid_arguments = ['home', 'ssi', 'model_test', 'iridis', 'iridis2']

class getArgs:
    """
    Getting the commandline arguments and return them
    """
    def __init__(self, description):
        """
        Params:
        -------
        :description str(): getting the description message for the line argument
        """
        self.description = description


    def return_arguments(self):
        """
        """
        parser = argparse.ArgumentParser(description=self.description)

        parser.add_argument("-e", "--env",
                            type=str, default="home",
                            help='Correct arguments: {})'.format(valid_arguments))

        args = parser.parse_args()

        if args.env == 'home':
            return config.ConfigHome

        elif args.env == 'ssi':
            return config.ConfigSoton

        elif args.env == 'model_test':
            return config.ConfigDevModel

        elif args.env == 'iridis':
            return config.ConfigIridis

        elif args.env == 'iridis2':
            return config.ConfigIridis2

        else:
            raise ValueError('Invalid environment name')
