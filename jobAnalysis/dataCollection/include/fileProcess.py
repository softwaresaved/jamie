#!/usr/bin/env python
# encoding: utf-8

import os
import json
import itertools
import bs4
import string


class fileProcess(object):
    """
    To get access to files
    """

    def __init__(self, root_folder=None):
        """
        """
        self.table_punc = bytes.maketrans(str.encode(string.punctuation), b' '* len(string.punctuation))
        self.table_space = bytes.maketrans(bytes(' ', 'utf-8'), bytes('_', 'utf-8'))
        self.root_folder = root_folder

        self.matching_key = ['jobid', 'name', 'employer', 'location', 'salary',
                             'hours', 'contract', 'placed_on', 'closes',
                             'description',
                             'extra_type_role', 'extra_subject_area',
                             'extra_location']

    def transform_key(self, key_string):
        """
        """
        key_string = key_string.lower()
        key_string = str.encode(key_string, 'utf-8').translate(self.table_punc)
        key_string = key_string.translate(self.table_space)
        key_string = key_string.decode('utf-8')
        key_string = key_string.replace('_', ' ')
        key_string = key_string.rstrip()
        key_string = key_string.replace(' ', '_')
        return key_string

    def get_raw_content(self, file_name):
        """
        Parse the filename and output an object of the content
        """
        with open('{}/{}'.format(self.root_folder, file_name), 'r') as f:
            return f.read()

    def process_result(self, dict_, result, key):
        """
        """
        if result:
            dict_[key] = result
        return dict_

    def get_employer(self, soup, enhanced):
        """
        """
        employer = None
        try:
            employer = soup.find('h3').text
        except AttributeError:
            try:
                for emp in soup.find('a').get('href'):
                    if emp[:10] == '/employer/':
                        employer = emp[:10]
            except (AttributeError, TypeError):
                pass
        return employer

    def get_title(self, soup, enhanced):
        """
        """
        try:
            return soup.find('h1').text
        except AttributeError:
            return None

    def get_place(self, soup, enhanced):
        """
        """
        try:
            return soup.find('h3').text
        except AttributeError:
            return None

    def get_details(self, soup, enhanced):
        """
        """
        table_to_match = 'td'
        class_to_match = 'detail-heading'

        for element in soup.findAll(table_to_match, {'class': class_to_match}):
            key = element.text
            key = self.transform_key(key)
            content = element.findNext('td')
            content = content.text
            yield {key: content}

    def get_description(self, soup, enhanced):
        """
        Get the description, aka main text from the file
        """
        # To add space when encounter <p> and <br> tags otherwise words are
        # attached
        # Some ads have the first div as <div id='enhanced-content'> which
        # change the structure of the html
        if enhanced == 'enhanced':
            try:
                section = soup.findAll('div', {'class': 'section', 'id': None})[0]
                return section.get_text(separator=u' ')
            except IndexError:
                pass
            try:
                section = soup.findAll('div', {'id': 'enhanced-right'})[0]
                return section.get_text(separator=u' ')
            except IndexError:
                pass
            try:
                section = soup.findAll('div', {'id': 'enhanced-content'})[0]
                return section.get_text(separator=u' ')
            except IndexError:
                print(soup)
                raise

        else:
            try:
                section = soup.findAll('div', {'class': 'section', 'id': None})[1]
                return section.get_text(separator=u' ')
            except IndexError:
                pass
            try:
                description_text = []
                section = soup.find('div', {'class': 'col-lg-12'})
                # Need to find the first <p>. The description is under that one
                # but also contains differents tags
                text_desc = False
                for description in section.findAll():
                    if description.name == 'p' and text_desc is False:
                        text_desc = True
                    if text_desc is True:
                        description_text.append(description.text)
                return ' '.join(description_text)
            except AttributeError:
                pass

    def get_extra_details(self, soup, enhanced):
        """
        Get the extra details at the end of description
        """

        for section in soup.findAll('div', {'class': 'inlineBox'}):
            key = section.find('p')
            if key:
                original_content = key.findNext('p')
                key = self.transform_key(key.text)
                result = list()
                for element in original_content.findAll('a'):
                    result.append(element.text)
                # Sometime the content is not within a tag <p> and
                # within <a> tag but under a
                # <div class='j-nav-pill-box'> tags
                # Check if the previous one give results and if not
                # try to parse the <div> tag
                # Work for <p>Subject Area(s) don't know for the others
                if len(result) == 0:
                    second_content = section.findNext('div')
                    for element in second_content.findAll('a'):
                        result.append(element.text)
                    if len(result) == 0:
                        result = original_content.text
                yield {'extra_{}'.format(key): result}


    def get_extra_details_enhanced(self, soup):
        """
        """
        for element in soup.findAll('td', {'class': 'detail-heading'}):
            key = element.text
            key = self.transform_key(key)
            content = element.findNext('td')
            content = content.text
            yield {key: content}

    def parse_html(self, dict_output, soup):
        """
        """
        if soup.find('div', {'id': 'enhanced-content'}):
            enhanced = 'enhanced'
        else:
            enhanced = 'normal'

        dict_output['enhanced'] = enhanced

        key = 'description'
        result = self.get_description(soup, enhanced)
        dict_output = self.process_result(dict_output, result, key)

        key = 'employer'
        result = self.get_employer(soup, enhanced)
        dict_output = self.process_result(dict_output, result, key)

        key = 'name'
        result = self.get_title(soup, enhanced)
        dict_output = self.process_result(dict_output, result, key)

        key = 'location'
        result = self.get_place(soup, enhanced)
        dict_output = self.process_result(dict_output, result, key)

        for details in self.get_details(soup, enhanced):
            dict_output.update(details)


        # Only present if not enhanced-content
        if enhanced is True:
            for extra_details in self.get_extra_details_enhanced(soup):
                dict_output.update(extra_details)
        else:
            for extra_details in self.get_extra_details(soup, enhanced):
                dict_output.update(extra_details)
        return dict_output

    def _extract_json_ads(self, data):
        """
        Get the json content from the page and return a dictionary from it
        """
        content_json = data.find('script', attrs={'type': 'application/ld+json'})
        try:
            content_json = content_json.contents[0]
            d = json.loads(content_json)
            return d
        except AttributeError:
            return None

    def get_new_subject_area(self, soup):

        subject = soup.find(lambda tag:tag.name=="b" and "Subject Area(s):" in tag.text)
        if subject is not None:
            list_subject = list()
            while True:
                # find the next subject which not contain the value but it is just before
                # the input that does have the value
                subject = subject.findNext('input', attrs={'name': 'categoryId[]'})
                try:
                    list_subject.append(subject.findNext('input')['value'])
                except AttributeError:  # means it is the end of the list
                    break
            return list_subject

    def get_new_extra_location(self, soup):

        for tag in soup.find_all('input', attrs={'class': 'j-form-input__location'}):
            return tag['value']

    def get_new_type_role(self, soup):

        type_role = soup.find(lambda tag:tag.name=="b" and "Type / Role:" in tag.text)
        if type_role is not None:
            list_type_role = list()
            while True:
                # find the next type_role which not contain the value but it is just before
                # the input that does have the value
                type_role = type_role.findNext('input', attrs={'name': 'jobTypeId[]'})
                try:
                    list_type_role.append(type_role.findNext('input')['value'])
                except AttributeError:  # means it is the end of the list
                    break
            return list_type_role

    def parse_json(self, dict_output, soup):
        """
        """
        try:
            dict_output['job_title'] = dict_output['json']['title']
        except KeyError:
            pass
        try:
            dict_output['employer'] = dict_output['json']['hiringOrganization']['name']
        except KeyError:
            pass
        try:
            dict_output['department'] = dict_output['json']['hiringOrganization']['department']['name']
        except KeyError:
            pass
        try:
            dict_output['location'] = dict_output['json']['jobLocation']['address']['addressLocality']
        except KeyError:
            pass
        try:
            dict_output['salary'] = dict_output['json']['baseSalary']['value']
        except KeyError:
            pass
        try:
            hours_contract = dict_output['json']['employmentType']
            splitted = hours_contract.split(',')
            # The hours and the contract are stored in the same k:v
            # Sometime when part time and full time are both available, the first
            # two elements are them. The last one is always the contract
            dict_output['hours'] = splitted[:-1]
            dict_output['contract'] =  splitted[-1]
        except KeyError:
            pass
        try:
            dict_output['placed_on'] = dict_output['json']['datePosted']
        except KeyError:
            pass
        try:
            dict_output['closes'] = dict_output['json']['validThrough']
        except KeyError:
            pass
        try:
            dict_output['description'] = dict_output['json']['description']
        except KeyError:
            pass
        try:
            dict_output['region'] = dict_output['json']['jobLocation']['address']['addressRegion']
        except KeyError:
            pass

        dict_output['subject_area'] = self.get_new_subject_area(soup)
        dict_output['extra_location'] = self.get_new_extra_location(soup)
        dict_output['type_role'] = self.get_new_type_role(soup)
        return dict_output


    def run(self, jobid, document=None):
        """
        """
        dict_output = dict()
        if document is None:
            dict_output['jobid'] = jobid
            raw_content = self.get_raw_content(jobid)
        else:
            dict_output['jobid'] = jobid
            raw_content = document

        if raw_content:
            soup = bs4.BeautifulSoup(raw_content, 'html.parser')
            # Check if there is a presence of a json dictionary which means
            # the new type of jobs
            raw_json = self._extract_json_ads(soup)
            if raw_json:
                dict_output['enhanced'] = 'json'
                dict_output['json'] = raw_json
                dict_output = self.parse_json(dict_output, soup)
            # Keep that version for old type of content and compatibility for
            # Previous version
            else:
                dict_output = self.parse_html(dict_output, soup)
        return dict_output


def main():
    """
    """
    def get_filename(root_folder, *args):
        """ Return the name of the file to be open in the csv reader """
        for dirname, subdir, files in os.walk(root_folder):
            for file_ in files:
                if file_ not in itertools.chain(*args):
                    yield file_

    INPUT_FOLDER = '/home/olivier/data/job_analysis/dev-bob/jobs'
    fileProc = fileProcess(INPUT_FOLDER)
    for filename in get_filename(INPUT_FOLDER):
        result = fileProc.run(filename)
        try:
            result['description']
        except KeyError:
            pass


if __name__ == '__main__':
    main()
