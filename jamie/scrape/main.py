#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to scrap the different jobs on https://www.jobs.ac.uk
"""
import os
import requests
from bs4 import BeautifulSoup
from ..lib import make_sure_path_exists
from ..logger import logger

logger = logger(name="scrape", stream_level="DEBUG")

content_attrs = [
    {"attrs_id": "class", "attrs_content": "content"},
    {"attrs_id": "id", "attrs_content": "enhanced-content"},
]


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


def split_by_results(data, divider="j-search-result__text"):
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
    return job.a["href"]


def split_info_from_job_url(BASE_URL, job_rel_url):
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
    :returns:
        bool: True if not present, False if present
    """
    filename = os.path.join(input_folder, job_id)
    if not os.path.isfile(filename):
        return True
    else:
        with open(filename, "r") as f:
            check_content = f.read()
            if check_content is None:
                logger.info("{}: No data recorded".format(filename))
                return True


def _extract_ads(data, attrs_id, attrs_content):
    """
    Extract the div that contains the data in the beautiful object ads. Try if the data is under the div class
    'content'. If it is not, it returns itself with the div_class set
    up with 'enhanced-content'
    :params:
        data bs4 obj: job ads
        attrs_id str: the type of tag for div. by default it is class
        attrs_content str: the data is either within the div_class 'content'
        or div id='enhanced-content'. By default it check the 'content'
    :returns:
        bs4 object : only the div that contains the information. Empty document if not found anything
    """
    return data.find_all("div", attrs={attrs_id: attrs_content})


def extract_ads_info(data):
    for attrs in content_attrs:
        content = _extract_ads(data, attrs["attrs_id"], attrs["attrs_content"])
        if len(content) > 0:
            return content


def new_extract_ads_info(data):
    """
    Return the body of the html page
    """
    data_to_return = data.find_all("body")
    if len(data_to_return) == 0:
        data_to_return = data.find_all("html")
    return data_to_return


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
    str_data = str(data)
    if len(str_data) > 100:
        with open(filename, "w") as f:
            f.write(str_data)
    else:
        print(str_data)
        raise


def main(config):
    """
    """
    # Get the folder or the file where the input data are stored
    input_folder = config["scrape.folder"]

    # Check if the folder exists
    logger.info("Check if the input folder exists: {}".format(input_folder))
    make_sure_path_exists(input_folder)

    # Setting the URL.
    # Number of jobs fetch for one query
    NUM_JOBS = config["scrape.njobs"]
    BASE_URL = "http://www.jobs.ac.uk"
    FULL_URL = "{}/search/?keywords=*&sort=re&s=1&pageSize={}".format(
        BASE_URL, NUM_JOBS
    )

    # Start the job collection
    logger.info("Getting the search page")
    page = get_page(FULL_URL)
    data = transform_txt_in_bs4(page)

    jobs_list = split_by_results(data)
    logger.info("Start to download new jobs")
    n = 0
    # file_process = fileProcess()
    for job in jobs_list:
        job_rel_url = extract_job_url(job)
        jobid, job_name, job_full_url = split_info_from_job_url(BASE_URL, job_rel_url)
        # Check if the jobid is not parsed yet
        if to_download(input_folder, jobid) is True:
            logger.info("Job id: {}".format(jobid))
            job_page = get_page(job_full_url)
            job_data = transform_txt_in_bs4(job_page)
            data_to_record = new_extract_ads_info(job_data)
            if data_to_record is None:
                data_to_record = extract_ads_info(job_data)
            if data_to_record is None:
                raise
            record_data(input_folder, jobid, data_to_record)
            n += 1
            logger.info("Jobs downloaded: {}".format(n))
