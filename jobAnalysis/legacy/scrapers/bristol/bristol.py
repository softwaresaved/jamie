
#-*- coding: utf-8 -*-
# Author: Schicheng Zhang (s1570551@sms.ed.ac.uk) <--- if you have a more permanent email messsage use that
'''
This script scrapes jobs from the University of Bristol website.
The url of job list is modified to display all the jobs in one page:
https://emea3.recruitmentplatform.com/syndicated/lay/jsoutputinitrapido.cfm?component=lay9999_lst400a&page=jsoutputinitrapido.cfm&ID=Q50FK026203F3VBQBV7V77V83&Resultsperpage=999&lg=UK&mask=uobext&pagenum=1&option=28&sort=DESC
The "Resultsperpage" parameter in the above url of is set to 999 to meet this requirement.
'''
import datetime, time, bs4, urllib2, smtplib
import re # for regular expression
from bs4 import BeautifulSoup
import os.path, os

# Parameters definition
file_location = '/root/jobs-analysis/MSc/PPP/Scrapers/'
#file_location = ''

class university_info:
    def __init__(self, name, url, category, code, last_number):        
        # Name of the university 
        self.name = name

        # Job list page url
        self.url = url

        # Job list type
        self.category = category

        # Job unified code
        # Used to merge database
        self.code = code

        # The job number of the last job scraped 
        self.last_number = last_number

    def get_university(self):
        return str(self.name)

    def get_url(self):
        return str(self.url)

    def get_category(self):
        return str(self.category)

    def get_code(self):
        return str(self.code)

    def get_last_number(self):
        return str(self.last_number)


# Create objects of university information
def obtain_progress(location, universities):

    progress_list = file(str(location) + 'progress.txt').readlines()

    # Put progress information into university objects
    for progress in progress_list:
        progress = progress.strip().split(',')
        if progress[0] != 'University':
            i = 0
            universities.append(university_info(progress[0],progress[1],progress[2],progress[3],progress[4]))
            i = i + 1

# Function to obtain the jobs list
def obtain_page_html(page_url):
    page_url = str(page_url)
    print ('start download from')
    print page_url
    page_html = urllib2.urlopen(urllib2.Request(page_url)) 

    # Use beautifulsoup to parse the content
    page_html = BeautifulSoup(page_html.read(),'html.parser')
    print 'Page obtained'
    return page_html

def obtain_job_list(page_html, university_code):
    job_list = ''
    #page_html = BeautifulSoup(str(page_html0))

    # Jobs on this website is organised in odd list and even list.

    job_list_odd = page_html.findAll('tr', {'class':'Lst-BG1'})
    for job in job_list_odd:

        # Obtain job title
        job_name = job.find('a', {'class':'lstA-desc1'}).renderContents()
        job_name = str(job_name).replace(',',' ').replace('&amp;',';')
        #print job_name

        # Obtain job url
        job_urls = job.findAll('a', {'class':'lstA-desc1'})
        for job_url in job_urls:
            job_url = job_url['href']

        # The replace statement is used because sometime there are unwanted wrap in job title sometimes
        job_list = job_list + str(job_name).replace('\n', '') + ',' + str(job_url) + ',' + str(university_code) + '\n' 

    job_list_even = page_html.findAll('tr', {'class':'Lst-BG2'})
    for job in job_list_even:

        # Obtain the job title
        job_name = job.find('a', {'class':'lstA-desc2'}).renderContents()
        job_name = str(job_name).replace(',',' ').replace('&amp;',';')

        # Obtain the job url
        job_urls = job.findAll('a', {'class':'lstA-desc2'})
        for job_url in job_urls:
            job_url = job_url['href']

        # This replace statement is used because sometimes there are unwanted line wrap in the job title.
        job_list = job_list + str(job_name).replace('\n','') + ',' + str(job_url) + ',' + str(university_code) + '\n'


    list_output = open(file_location + 'job_list.csv', 'w')
    list_output.write(job_list)
    list_output.close()
    print 'Job list created'


def obtain_employer_info(job_list, universities):
        # find which university to scrape
    for university in universities:

        # This can be optimized, don't need to pass the whole list to this function
        # print str(job_list[0]).replace('\n','').split(',')[2]
        # print university.code
        if university.code == str(job_list[0]).replace('\n', '').split(',')[2]:
            employer_url_prefix = str(university.url.split('?')[0])
            employer_name = str(university.name)
            employer_code = str(university.code)
    employer_info = [employer_url_prefix, employer_name, employer_code]
    return employer_info

def save_jd_page(job_list, employer_info):

    if(os.path.isfile(file_location + 'scraped_list.csv')):
        open_method2 = 'a'
        scraped_list = file(file_location + 'scraped_list.csv','r')
        scraped_list = scraped_list.readlines()
    else:
        open_method2 = 'w'
        scraped_list = []
    scraped_output = open(file_location + 'scraped_list.csv',open_method2)
    for job in job_list:
        #list check should be checked here
        if job not in scraped_list:
            #reset buffers
            job_detail_url = ''
            job_detail_page = ''
            job_detail = ''
            scraped_log = ''
            job_number = ''

            job_detail_url = str(employer_info[0]) + '?' + str(str(job.split(',')[1]).split('?')[1])
            job_detail_page = obtain_page_html(job_detail_url)
            job_detail = collect_detail(job_detail_page,employer_info)

            #Save original html file to local
            job_number = str(job_detail_page.find('span', {'id':'JDText-Param2'}).renderContents())
            orignial_job_page = open(file_location + 'original_detail/' + dt + '_'  + employer_info[2] + '_' + job_number + '.html','w')
            orignial_job_page.write(str(job_detail_page))
            #original_job_page.close()


            # Update scraped list here
            scraped_log = str(job_detail.split('|')[3]).replace('&amp;',';').replace(',',' ') + ',' + str(job.split(',')[1]) + ',' + str(job_detail.split('|')[2]) + '\n'
            scraped_output.write(scraped_log)
        else:
            print 'job scraped before'

    scraped_output.close()

# Extract job detail from job detail page
def collect_detail(job_detail_page, employer_info,datestamp):
    job_title = str(job_detail_page.find('h3', {'class':'JD-Title'}).renderContents()).replace('\n','').replace('&amp;',';')
    job_number = str(job_detail_page.find('span', {'id':'JDText-Param2'}).renderContents())
    if (re.match('EXTERNAL', job_number)):
        job_division = 'External'
    else:
        job_division = str(job_detail_page.find('span', {'id':'JDText-Param3'}).renderContents()).replace('&amp;',';')
    job_contract_type = str(job_detail_page.find('span', {'id':'JDText-Param4'}).renderContents())
    job_working_pattern = str(job_detail_page.find('span', {'id':'JDText-Param5'}).renderContents())
    job_salary = str(job_detail_page.find('span',{'id':'JDText-Param6'}).renderContents())
    #print job_salary + job_title + job_number
    if ('£' not in job_salary):
        job_min_salary = 'Not Listed'
        job_max_salary = 'Not Listed'
    else:

        # The following part can be replaced with regular expression
        # Note that the pound sign may appear like "&#163;" in some cases
        if len(job_salary.split('£')) >= 3:
            job_min_salary = str(str(job_salary.split('£')[1]).replace(',', '').replace(' - ', ''))
            job_min_salary = str(re.sub('[^0-9]','',job_min_salary))
            job_max_salary = str(str(str(job_salary.split('£')[2]).split(' ')[0]).replace(',', ''))
            job_max_salary = str(re.sub('[^0-9]','',job_max_salary))
        else:
            job_min_salary = str(str(str(job_salary.split('£')[1]).split(' ')[0]).replace(',', ''))
            job_max_salary = job_min_salary

    deadline = str(job_detail_page.find('span', {'id':'JDText-Param7'}).renderContents())

    # Note that in some system '\r' is used to start a new line despite it may appears like '^M'
    job_description = str(BeautifulSoup(str(job_detail_page.find('span', {'id':'JDText-Field2'})).replace('<br>', '').replace('</br>', '').replace('\r', ''),'html.parser').get_text().encode('utf-8')).replace('\n', '')
    job_detail = datestamp + '|' + str(employer_info[1]) + '|' + str(employer_info[2]) + '|' + job_title + '|' + job_number + '|' + \
                 job_division + '|' + job_contract_type + '|' + job_working_pattern + '|' + \
                 job_min_salary + '|' + job_max_salary + '|' + deadline + '|' + job_description + '\n'

    return str(job_detail)


def obtain_new_jobs(datestamp):
    os.system('ls ' + file_location + 'original_detail/ | grep ' + str(datestamp) + ' > ' + file_location + 'new_job_list.txt')
    new_job_list = file(file_location + 'new_job_list.txt', 'r')
    new_job_list = new_job_list.readlines()

    return new_job_list


if __name__ == '__main__':

    # Obtain the current date
    dt = str(datetime.date.today() - datetime.timedelta(days=1)).replace('-', '')

    # Create a list of universities
    universities = []
    obtain_progress(file_location, universities)

    # Obtain job list
    job_list_page = obtain_page_html(universities[0].url)
    obtain_job_list(job_list_page, universities[0].code)

    job_list = file(file_location + 'job_list.csv', 'r').readlines()

    # Obtain jobs according to job list
    employer_info = obtain_employer_info(job_list, universities)
    save_jd_page(job_list, employer_info)

    print 'All job decriptions are saved to local'

    # Check if job_detail.csv exists
    if(os.path.isfile(file_location + 'job_detail.csv')):
        open_method = 'a'
    else:
        open_method = 'w'
    detail_output = open(file_location + 'job_detail.csv',open_method)
    if open_method == 'w':
        table_title = 'Scraped_date|University_name|University_code|Job_name|Reference_id|Division|Contract_type|Working_pattern|Minimum_salary|Maxmium_salary|Deadline|Job_description\n'
        detail_output.write(table_title)

    # Obtain files that are scraped today
    new_jobs = obtain_new_jobs(dt)
    for new_job in new_jobs:
        new_job = str(new_job).replace('\n','')
        new_job_page = BeautifulSoup(file(file_location + 'original_detail/' + new_job,'r').read(),'html.parser')
        datestamp = new_job.split('_')[0]
        detail_output.write(collect_detail(new_job_page,employer_info,datestamp))

    detail_output.close()

    print 'job_detail.csv updated'


    print 'Date: ' + dt +' Job finished!'
