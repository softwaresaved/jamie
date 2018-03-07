# Scraper for the University of Cambridge Jobs
This is a web crawling program which collects job information from the University of Cambridge.
This README.MD illustrates the process of this program.

**NOTE**: There can be duplicates in the data. Thus data cleaning process is 
required before the data can be used for classification.

## Files
* `cambridge.py` - main scraping program.
* `progress.txt` - stores the information of universities with four columns: 
   1. uni's name, 
   2. url of job list, 
   3. job category (if applicable in some uni) and 
   4. uni's code.

The following directories/files are generated when the script is run:

* `job_list.csv` -  all the jobs that currently listed on the website of the uni. 
   This file is recreated every time the program runs.
* `scraped_list` - records jobs that has been saved to local
* `new_job_list.txt` - temporarily reords the file name of new jobs. 
   This file is recreated every time the program runs.
* `job_detail.csv` - Collected information will be saved to this file ultimately.
* `original_detail/` - a folder used to store original job detail page html. 
   Files are named following the pattern of "date_code_referenceid.html".

