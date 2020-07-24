#!/usr/bin/env python
# encoding: utf-8

import os
import json
import itertools
import bs4
import string
from pathlib import Path
from typing import Union


_table_punc = bytes.maketrans(str.encode(string.punctuation), b' ' * \  # NOQA
                              len(string.punctuation))
_table_space = bytes.maketrans(bytes(' ', 'utf-8'), bytes('_', 'utf-8'))

class JobFile:
    """
    Represents a single jobs.ac.uk scraped document

    Parameters
    ----------
    content : Path or str
        If type Path, filename of jobs.ac.uk scraped document, or if str,
        the content itself

    Attributes
    ----------
    data : dict
        Parsed data from HTML content
    """

    _matching_key = ['jobid', 'name', 'employer', 'location', 'salary',
                     'hours', 'contract', 'placed_on', 'closes',
                     'description', 'extra_type_role',
                     'extra_subject_area', 'extra_location']
    data = dict()

    def __init__(self, content: Union[Path, str]):
        if isinstance(content, Path):
            self.filename = content
            self._content = self.filename.read_text()
        elif isinstance(content, str):
            self._content = content
        else:
            raise ValueError("content must be one of Path or str")
        self._soup = bs4.BeautifulSoup(self._content, 'html.parser')

        # Enhanced content alters behaviour of some parsing
        if soup.find('div', {'id': 'enhanced-content'}):
            self.enhanced = True
        else:
            self.enhanced = False

    @staticmethod
    def transform_key(self, key_string):
        key_string = key_string.lower()
        key_string = str.encode(key_string, 'utf-8').translate(self.table_punc)
        key_string = key_string.translate(self.table_space)
        key_string = key_string.decode('utf-8')
        key_string = key_string.replace('_', ' ')
        key_string = key_string.rstrip()
        key_string = key_string.replace(' ', '_')
        return key_string

    @property
    def employer(self):
        _employer = None
        try:
            _employer = self._soup.find('h3').text
        except AttributeError:
            try:
                for emp in self._soup.find('a').get('href'):
                    if emp[:10] == '/employer/':
                        _employer = emp[:10]
            except (AttributeError, TypeError):
                pass
        return _employer

    @property
    def job_title(self):
        try:
            return self._soup.find('h1').text
        except AttributeError:
            return None

    @property
    def place(self):
        try:
            return self._soup.find('h3').text
        except AttributeError:
            return None

    def details(self):
        table_to_match = 'td'
        class_to_match = 'detail-heading'

        for element in self._soup.findAll(table_to_match, {'class': class_to_match}):
            key = element.text
            key = self.transform_key(key)
            content = element.findNext('td')
            content = content.text
            yield {key: content}

    @property
    def description(self, soup, enhanced):
        # To add space when encounter <p> and <br> tags otherwise words are
        # attached
        # Some ads have the first div as <div id='enhanced-content'> which
        # change the structure of the html
        if self.enhanced:
            try:
                section = self._soup.findAll('div', {'class': 'section', 'id': None})[0]
                return section.get_text(separator=u' ')
            except IndexError:
                pass
            try:
                section = self._soup.findAll('div', {'id': 'enhanced-right'})[0]
                return section.get_text(separator=u' ')
            except IndexError:
                pass
            try:
                section = self._soup.findAll('div', {'id': 'enhanced-content'})[0]
                return section.get_text(separator=u' ')
            except IndexError:
                print(soup)
                raise

        else:
            try:
                section = self._soup.findAll('div', {'class': 'section', 'id': None})[1]
                return section.get_text(separator=u' ')
            except IndexError:
                pass
            try:
                section = self._soup.findAll('div', {'id': 'job-description'})[1]
                return section.get_text(separator=u' ')
            except IndexError:
                pass
 
            try:
                description_text = []
                section = self._soup.find('div', {'class': 'col-lg-12'})
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

    def extra_details(self):
        """
        Get the extra details at the end of description
        """
        if not self.enhanced:
            for section in self._soup.findAll('div', {'class': 'inlineBox'}):
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
        else:
            for element in self._soup.findAll('td', {'class': 'detail-heading'}):
                key = element.text
                key = self.transform_key(key)
                content = element.findNext('td')
                content = content.text
                yield {key: content}

    def parse(self):
        self.data = {
            'description': self.description,
            'employer': self.employer,
            'name': self.job_title,
            'location': self.place,
        }
        for d in self.details():
            self.data.update(d)

        for extra_details in self.extra_details():
            self.data.update(extra_details)
        return self.data

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
            dict_output['name'] = dict_output['json']['title']
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
        except TypeError:  # The job location seems to appears sometimes in a list. However that list contains the same dictionary
            try:
                dict_location = dict_output['json']['jobLocation'][0]
                dict_output['location'] = dict_location['address']['addressLocality']
            except IndexError:
                pass
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

        except TypeError:  # The job location seems to appears sometimes in a list. However that list contains the same dictionary
            try:
                dict_region = dict_output['json']['jobLocation'][0]
                dict_output['location'] = dict_location['address']['addressRegion']
            except IndexError:
                pass
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
