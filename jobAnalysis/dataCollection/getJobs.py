#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to scrap the different jobs on https://www.jobs.ac.uk
"""
import os
import errno
import argparse

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path

sys.path.append(str(Path(".").absolute().parent))

from common.logger import logger
from common.configParser import configParserPerso as configParser

logger = logger(name="getJobs", stream_level="DEBUG")


# Setting the URL.
BASE_URL = "http://www.jobs.ac.uk"
# Number of jobs fetch for one query
NUM_JOBS = 10
FULL_URL = "{}/search/?keywords=*&sort=re&s=1&show={}".format(BASE_URL, NUM_JOBS)


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def get_page(url):
    """
    Use request to get an URL page
    :params:
        url str: the URL to parse
    :returns:
        requests object text
    """
    page = requests.get(url)
    return page.text


def transform_txt_in_bs4(data):
    """
    Get the json data from a request object
    and read the data
    :params:
        data str: containing the data from request
    :returns:
        a beautifulSoup object
    """
    return BeautifulSoup(data, "html.parser")


def split_by_results(data, divider="result"):
    """
    Get an bs4 object and return a generator that split
    the text with the balise <div class="result"> by defautl
    :params:
        data bs4 obj: contain the data itself
        divider str(): the div class that split the data.
        Default is the class "result"
    :output:
        generator of the same data but split with the divider
    """
    for job in data.find_all("div", attrs={"class": divider}):
        yield job


def extract_job_url(job):
    """
    parse the job data and extract the str for the URL of the job posted
    params:
        job str: html str representation from bs4
    returns:
        url str: relative URL path of the job ad
    """
    for i in job.find_all("div", attrs={"class": "text"}):
        for link in i.find_all("a", href=True):
            return link["href"]


def split_info_from_job_url(job_rel_url):
    """
    Split the job_rel_url to get the separated info and
    create a full URL by combining the BASE_URL and the job_rel_url
    :params:
        job_rel_url str: contain the Relative Job URL
    :returns:
        job_id str: the unique id contained in the job_rel_url
        job_name str: the name of the job
        job_full_url str: full URL of the job ads
    """
    splitted_url = [i for i in job_rel_url.split("/") if i]
    # The first element of the list is 'job' as the structure
    # of the string is like this:
    # /job/BJR877/assistant-professor-associate-professor-full-professor-in-computational-environmental-sciences-and-engineering/
    if len(splitted_url) != 3:
        raise
    job_id = splitted_url[1]
    job_name = splitted_url[2]
    job_full_url = BASE_URL + job_rel_url
    return job_id, job_name, job_full_url


def to_download(input_folder, job_id):
    """
    Check in the input_folder if a file with the job_id exists
    if it is the case it return True
    :params:
        input_folder str: absolute path of directory where files are stored
        job_id str: unique id that is used by job.ac.uk for their job
        and in the mongodb to ensure that all ads are unique
    :returns:
        bool: True if not present, False if present
    """
    filename = os.path.join(input_folder, job_id)
    if not os.path.isfile(filename):
        return True


def extract_ads_info(data, div_class="content"):
    """
    Extract the div that contains the data in the
    beautiful object ads. Try if the data is under the div class
    'content'. If it is not, it returns itself with the div_class set
    up with 'enhanced-content'
    :params:
        data str: bs4 object of the job ads
        div_class str: the data is either within the div_class 'content'
        or 'enhanced-content'. By default it check the 'content'
    :returns:
        str: only the div that contain the information
    """
    for content in data.find_all("div", attrs={"class": div_class}):
        if content is None and div_class == "content":
            return extract_ads_info(data, div_class="enhanced-content")
        else:
            return content


def record_data(input_folder, job_id, data):
    """
    Recording data (html content) in a file with the job_id
    as filename
    :params:
        input_folder str: absolute path of the folder where to save the
        file
        job_id str: obtained from jobs.ac.uk and used as filename
        data bs4: html data in str() format to be saved in a file
    :output:
        None: record a file
    """
    filename = os.path.join(input_folder, job_id)
    with open(filename, "w") as f:
        f.write(data)


def main():
    """
    """
    parser = argparse.ArgumentParser(description="Collect jobs from jobs.ac.uk")

    parser.add_argument("-c", "--config", type=str, default="config_dev.ini")

    args = parser.parse_args()
    config_file = "../config/" + args.config

    # set up access credentials
    config_value = configParser()
    config_value.read(config_file)

    # Get the folder or the file where the input data are stored
    input_folder = config_value["input"].get("INPUT_FOLDER".lower(), None)
    # Check if the folder exists
    make_sure_path_exists(input_folder)

    # Start the job collection
    page = get_page(FULL_URL)
    data = transform_txt_in_bs4(page)
    jobs_list = split_by_results(data)
    for job in jobs_list:
        job_rel_url = extract_job_url(job)
        job_id, job_name, job_full_url = split_info_from_job_url(job_rel_url)
        # Check if the job_id is not parsed yet
        if to_download(input_folder, job_id) is True:
            job_page = get_page(job_full_url)
            job_data = transform_txt_in_bs4(job_page)
            data_to_record = extract_ads_info(job_data)
            record_data(input_folder, job_id, data_to_record)


if __name__ == "__main__":
    main()