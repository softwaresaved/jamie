#!/usr/bin/env python
# encoding: utf-8

import os
import itertools
import bs4
import string


class fileProcess(object):
    """
    To get access to files
    """

    def __init__(self, root_folder):
        """
        """
        self.table_punc = bytes.maketrans(str.encode(string.punctuation), b' '* len(string.punctuation))
        self.table_space = bytes.maketrans(bytes(' ', 'utf-8'), bytes('_', 'utf-8'))
        # self.count_fail = 0
        self.root_folder = root_folder

        self.matching_key = ['jobid', 'name', 'employer', 'location', 'salary',
                             'hours', 'contract', 'placed_on', 'closes',
                             'job_ref', 'description',
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
        try:
            return soup.find('h3').text
        except AttributeError:
            try:
                for employer in soup.find('a').get('href'):
                    if employer[:10] == '/employer/':
                        return employer[:10]
            except (AttributeError, TypeError):
                return None

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
        try:
            # To add space when encounter <p> and <br> tags otherwise words are
            # attached
            # Some ads have the first div as <div id='enhanced-content'> which
            # change the structure of the html
            if enhanced is True:
                section = soup.findAll('div', {'class': 'section', 'id': None})[0]
            else:
                section = soup.findAll('div', {'class': 'section', 'id': None})[1]

            return section.get_text(separator=u' ')
        except IndexError:
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
                if len(result) == 0:
                    print('Key: {}'.format(key))
                    print('Result: {}'.format(result))
                    print('Section: {}'.format(section))
                    print('Content: {}'.format(original_content.text))

                yield {'extra_{}'.format(key): result}

    def get_extra_details_enhanced(self, soup):
        """
        """
        # all_details = soup.findAll('div', {'class': 'advert-details-box'})
        # for box in all_details :
        #     for element in box.findAll('tr'):
        #         # for element in soup.findAll('table', {'class': 'advert-details'}):
        #         key = element.find('td', {'class': 'detail-heading'})
        #         transformed_key = self.transform_key(key.text)
        #         content = key.find_next_siblings()
        #         # content = element.find_next_siblings('td')
        #         print(transformed_key)
        #         content = content[0].text
        #         print(content)
        #         yield {transformed_key: content}
        for element in soup.findAll('td', {'class': 'detail-heading'}):
            key = element.text
            key = self.transform_key(key)
            content = element.findNext('td')
            content = content.text
            yield {key: content}

    def run(self, document):
        """
        """
        dict_output = dict()
        dict_output['jobid'] = document
        dict_output['enhanced'] = 'Not dealt with'
        dict_output['raw_content'] = self.get_raw_content(document)
        if dict_output['raw_content']:
            soup = bs4.BeautifulSoup(dict_output['raw_content'], 'html.parser')

            if soup.find('div', {'id': 'enhanced-content'}):
                enhanced = 'enhanced'
            else:
                enhanced = 'normal'

            dict_output['enhanced'] = enhanced
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

            key = 'description'
            result = self.get_description(soup, enhanced)

            dict_output = self.process_result(dict_output, result, key)
            # Only present if not enhanced-content
            if enhanced is True:
                for extra_details in self.get_extra_details_enhanced(soup):
                    dict_output.update(extra_details)
            else:
                for extra_details in self.get_extra_details(soup, enhanced):
                    dict_output.update(extra_details)
            return dict_output

        else:
            # record as error, empty file
            # still output ta dict with the name only
            # self.count_fail += 1
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
    n =1
    m =0
    for filename in get_filename(INPUT_FOLDER):
        result = fileProc.run(filename)
        try:
            result['description']
        except KeyError:
            pass

        # try:
        #     print('{} - {}'.format(result['extra_type_role'], n))
        #     n +=1
        # except KeyError:
        #     m+=1
        # if isinstance(result['extra_type_role'], list):
        # print(filename)


if __name__ == '__main__':
    main()
