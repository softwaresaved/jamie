#!/usr/bin/env python
# -*- coding: utf-8 -*-


""" Small scripts to transform the date received from the jobs.ac.uk into a strtime rather
than their format

"""

def remove_suffix_date(s):
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', str(s))


def transform_valid_date(s):
    return datetime.strptime(s, '%d %B %Y')


def get_month(date):
    """
    return the month from the formatting datestring
    23th June 2016
    """
    date_time_obj = transform_valid_date(remove_suffix_date(date))
    # Get only the year and the month and transforming str month into numbered month
    return date_time_obj.strftime('%Y-%m')

