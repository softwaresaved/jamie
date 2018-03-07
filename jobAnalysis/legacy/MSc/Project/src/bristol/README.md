# Scraper for the University of Bristol Jobs
This is a web crawling program which collect job information from the University of Bristol.
This README.md illustrates the process of this program.

**NOTE**: There can be duplicates in the data. Thus data cleaning process is 
required before the data can be used for classification.

## Files
* `bristol.py` - the main scraping program. 
* `progress.txt` - stores the information of universities in four columns: 
   1. uni's name, 
   2. url of job list, 
   3. job category (if applicable in some uni) and 
   4. uni's code.

The following files/directories will be created once the script is run:

* `job_list.csv` -  all the jobs that currently listed on the website of the uni. 
   This file is recreated every time the program runs.
* `scraped_list` - records jobs that have been saved to local storage.
* `new_job_list.txt` - temporarily records the file name of new jobs. This file is 
   recreated every time the program runs.
* `job_detail.csv` - Collected jobs will be saved to this file ultimately.
* `original_detail/` - a folder used to store original job detail page html. 
  Files are named following the pattern of "date_code_referenceid.html".

