#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to scrap the different jobs on https://www.jobs.ac.uk
"""

import requests
from bs4 import BeautifulSoup

# Setting the URL.
BASE_URL = "http://www.jobs.ac.uk"
# Number of jobs fetch for one query
NUM_JOBS = 10
FULL_URL = "{}/search/?keywords=*&sort=re&s=1&show={}".format(BASE_URL, NUM_JOBS)


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


def to_download(job_id):
    """
    Check the MongoDB if the job id has been already downloaded
    if it is the case it return True
    :params:
        job_id str: unique id that is used by job.ac.uk for their job
        and in the mongodb to ensure that all ads are unique
    :returns:
        bool: True if not present, False if present
    """
    # TODO
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


def main():
    """
    """
    page = get_page(FULL_URL)
    data = transform_txt_in_bs4(page)
    jobs_list = split_by_results(data)
    for job in jobs_list:
        job_rel_url = extract_job_url(job)
        job_id, job_name, job_full_url = split_info_from_job_url(job_rel_url)
        # Check if the job_id is not parsed yet
        if to_download(job_id) is True:
            job_page = get_page(job_full_url)
            job_data = transform_txt_in_bs4(job_page)
            data_to_record = extract_ads_info(job_data)
            print(data_to_record)


if __name__ == "__main__":
    main()
