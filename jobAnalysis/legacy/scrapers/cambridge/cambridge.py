
#-*- coding: utf-8 -*-
'''
This is is a web scrapper used to scrap job opportunities from the website of University of Cambridge.
http://www.jobs.cam.ac.uk/job/
'''
import datetime, time, bs4, urllib2, smtplib
import re # for regular expression
from bs4 import BeautifulSoup
import os.path, os

# Parameters definition
#file_location = '/root/jobs-analysis/MSc/PPP/Scrapers/cambridge/'
file_location = ''

class university_info:
    def __init__(self, name, url, category, code, last_number):        
        # Name of university 
        self.name = name

        # Job list page url
        self.url = url

        #Job list type
        self.category = category

        # Job unified code
        # Used to merge database
        self.code = code

        # The job number of the last scraped job
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

# Function for obtain job list
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

    job_list_html = page_html.find('table', {'class':'jobs sort'})
    job_list_html = job_list_html.findAll('tr')
    for job in job_list_html:

        # Obtain job id
        job_id = job.findAll('td')
        if len(job_id) == 3:
            job_id = str(job_id[1]).replace('<td>','').replace('</td>','')
            job_ddl = str(job_id[2]).replace('<td>','').replace('</td>','')
        # Obtain job url
            job_url = job.find('a')
            job_url = job_url['href']
        #print job_url
        
        # obtain closing date


        # The replace statement is used because sometime there are unwanted wrap in job title sometimes
            job_list = job_list + str(job_id) +  ',http://www.jobs.cam.ac.uk' + str(job_url) + ',' + str(job_ddl)  + '\n' 


    list_output = open(file_location + 'job_list.csv', 'w')
    list_output.write(job_list)
    list_output.close()
    print 'Job list created'


def obtain_employer_info(job_list, universities):
        # find which university to scrap
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

def save_jd_page(job_list, universities):

    if (not os.path.isdir(file_location + 'original_detail/')):
        os.system('mkdir original_detail')

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
            job_title = ''
            scraped_log = ''
            job_number = ''
            sidebar = ''
            reference_get = False
            job_detail_url =  str(job.split(',')[1])
            job_id = str(job.split(',')[0])
            job_ddl = str(job.split(',')[2])
            job_detail_page = obtain_page_html(job_detail_url)
            #job_detail = collect_detail(job_detail_page,employer_info)

            #Save original html file to local
            job_title = job_detail_page.findAll('h2')[1].getText()
            #print job_title
            sidebar = str(job_detail_page.find('aside', {'id':'sidebar'}).getText().encode('utf-8')).split('\n')
            for sidebar_info in sidebar:
                if reference_get:
                    job_number = str(sidebar_info)
                    #print job_number
                    reference_get = False
                if sidebar_info == 'Reference':
                    reference_get = True

            orignial_job_page = open(file_location + 'original_detail/' + dt + '_'  + universities.get_code() + '_' + job_number + '.html','w')
            orignial_job_page.write(str(job_detail_page))
            #original_job_page.close()


            # Update scraped list here
            scraped_log = str(job_id) + ',' + str(job_detail_url).replace('\n','') + ',' + str(job_ddl).replace('\n','') + '\n'
            scraped_output.write(scraped_log)
        else:
            print 'job scraped before'

    scraped_output.close()

# Extract job detail from job detail page
def collect_detail(job_detail_page, university,datestamp):
    reference_get = False
    division_get = False
    salary_get = False
    deadline_get = False

    job_title = str(job_detail_page.findAll('h2')[1].getText()).replace(',',';')
    job_description = str(job_detail_page.find('section', {'class':'grid_11 prefix_2 suffix_1 alpha'}).getText().encode('utf-8'))
    job_number = ''
    job_division = ''
    job_salary = ''
    deadline = ''

    sidebar = str(job_detail_page.find('aside', {'id':'sidebar'}).getText().encode('utf-8')).split('\n')
    for sidebar_info in sidebar:
        if reference_get:
            job_number = str(sidebar_info)
            #print job_number
            reference_get = False
        if division_get:
            job_division = str(sidebar_info).replace(',',';')
            #print job_number
            division_get = False
        if salary_get:
            job_salary = str(sidebar_info)
            #print job_number
            salary_get = False
        if deadline_get:
            deadline = str(sidebar_info)
            #print job_number
            deadline_get = False
        '''
        if category_get:
            category_get = str(sidebar_info)
            #print category_get
            category_get = False
        if publish_date_get:
            publish_date_get = str(sidebar_info)
            #print publish_date_get
            publish_date_get = False
        '''

        if sidebar_info == 'Reference':
            reference_get = True
        if sidebar_info == 'Department/Location':
            division_get = True
        if sidebar_info == 'Salary':
            salary_get = True
        if sidebar_info == 'Closing date':
            deadline_get = True

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


    # Note that in some system '\r' is used to start a new line despite it may appears like '^M'
    job_description = job_description.replace('\n', '')
    #print job_description
    job_detail = datestamp + '|' + str(university.get_university()) + '|' + str(university.get_code()) + '|' + job_title + '|' + job_number + '|' + \
                 job_division + '|' + 'Unknown' + '|' + 'Unknown' + '|' + \
                 job_min_salary + '|' + job_max_salary + '|' + deadline + '|' + job_description + '\n'

    return str(job_detail)


def obtain_new_jobs(datestamp):
    os.system('ls ' + file_location + 'original_detail/ | grep ' + str(datestamp) + ' > ' + file_location + 'new_job_list.txt')
    new_job_list = file(file_location + 'new_job_list.txt', 'r')
    new_job_list = new_job_list.readlines()

    return new_job_list


if __name__ == '__main__':

    # Obtain current date
    dt = str(datetime.date.today() - datetime.timedelta(days=1)).replace('-', '')

    # Create a list of universities
    universities = []
    obtain_progress(file_location, universities)
    print "progress obtained"

    # Obtain job list
    job_list_page = obtain_page_html(universities[0].url)
    obtain_job_list(job_list_page, universities[0].code)
    print "job page obtained"

    job_list = file(file_location + 'job_list.csv', 'r').readlines()

    # Obtain jobs according to job list
    save_jd_page(job_list, universities[0])

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

    # Obtain files that is scraped today
    new_jobs = obtain_new_jobs(dt)
    for new_job in new_jobs:
        new_job = str(new_job).replace('\n','')
        new_job_page = BeautifulSoup(file(file_location + 'original_detail/' + new_job,'r').read(),'html.parser')
        datestamp = new_job.split('_')[0]
        detail_output.write(collect_detail(new_job_page,universities[0],datestamp))

    detail_output.close()

    print 'job_detail.csv updated'


    print 'Job finished!'
