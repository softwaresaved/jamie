"""

This Python 3 script cleans an input jobs dictionary and outputs a cleaned jobs dictionary.


"""

import re
import csv
import difflib
from operator import itemgetter
from pathlib import Path
from datetime import datetime
from ..common.textClean import textClean
from ..data import datasets


class OutputRow:
    """
    A class that receive a dictionary as input. It checks several keys and operate additional
    cleaning operation. When the target keys are not present or the content is wrong, a list of error
    is generated and recorded.
    Return the cleaned dictionary and the key with the invalid code with it
    """

    def __init__(self, input_row, dataset='uk_uni'):
        """
        *Create attributes from the dict() input_row
        *Import the transformKey __init__() to have access to the key list
        * Transform the key of the input_row to the defined ones in TransformKey
        * Create a list of new key to add after cleaning process
        """
        # Create attribute from the input_row
        self.input_row = input_row
        self.dataset = dataset

        self.needed_keys = ['jobid',
                            'description',
                            'job_title',
                            'employer',
                            'location',
                            'salary',
                            'funding_amount',
                            'hours',
                            'contract',
                            'placed_on',
                            'closes',
                            'subject_area']

        # Create a list of keys that are added during the cleaning process
        self.new_keys = ['invalid_code',
                         'salary_min',
                         'salary_max',
                         'duration_ad_days',
                         'uk_university',
                         'uk_postcode',
                         'salary_median',
                         'not_student',
                         'in_uk']
        # Create a list for all the keys that are going to be recorded in the database
        # populate it with the new_keys and the first
        self.keys_to_record = list(self.new_keys)
        self.create_dictionary()
        self.invalid_code = list()
        # get the list of university from the file ./uk_uni_list.txt for the method
        # self.add_uk_university
        self.text_cleaner = textClean()
        self.uk_uni_list = self.read_uni_list_file()
        self.uk_postcode_dict = self.read_postcode()

    def read_uni_list_file(self):
        """
        Read the txt file containing all universities from a text file
        and create a set of strings
        """
        return set(' '.join(set([x for x in self.text_cleaner.clean_text(l)]))
                   for l in datasets[self.dataset].list)

    def read_postcode(self):
        """
        Read the csv file containing university and postcode for UK only
        """
        return {row.PROVIDER_NAME: row.POSTCODE
                for row in datasets[self.dataset].postcodes.itertuples()}

    def matching_key(self, key):
        """
        Check if a key match a better name
        """
        key = key.rstrip().lower()

        if key == 'contract_type' or key == 'contract' or key == 'contract type':
            clean_key = 'contract'

        elif key == 'expires' or key == 'closes':
            clean_key = 'closes'

        elif key == 'placed on':
            clean_key = 'placed_on'

        elif key == 'name':
            clean_key = 'job_title'
        elif key == 'type___role' or key == 'extra_type___role':
            clean_key = 'type_role'
        elif key == 'subject_area_s' or key == 'subject_area' or key == 'extra_subject_area' or key == 'extra_subject_area_s':
            clean_key = 'subject_area'
        elif key == 'location_s' or key == 'location':
            clean_key = 'location'
        elif key == 'extra_location_s':
            clean_key = 'extra_location'
        else:
            clean_key = key
        return clean_key

    def create_dictionary(self):
        """
        Parse the input_row and set up the attribute of
        the object with the key value
        When it finisheds set up the keys from self.needed_keys
        that are not present to empty string
        for the invalid_code
        """
        for key in self.input_row:
            cleaned_key = self.matching_key(key)
            try:
                setattr(self, cleaned_key, self.input_row[key])
                self.keys_to_record.append(cleaned_key)
            except KeyError:
                setattr(self, key, None)

        for key in self.needed_keys:
            try:
                getattr(self, key)
            except AttributeError:
                setattr(self, key, '')

    @staticmethod
    def remove_suffix_date(s):
        """
        Remove the st, th,... added to a string containing
        a date
        :params:
            s str(): containing the string representation
                        of the date
        :return:
            str() without the st, th
        """
        return re.sub(r'(\d)(st|nd|rd|th)', r'\1', str(s))

    @staticmethod
    def transform_valid_date(s):
        """
        Transform a string into a datetime object
        Suppose to receive a string in two formats:
                - 17th July 2018
                - 2018-07-17
                - 2018-10-07T00:00:00+00:00


        :params:
            s str(): containing the string representation of
                        an date time object
        :return:
            a datetime object if valid. The str itself if transformation
            failed
        """
        try:
            return datetime.strptime(s, '%d %B %Y')
        except ValueError:
            try:
                return datetime.strptime(s.replace(' ', '').strip(), "%Y-%m-%d")
            except ValueError:
                try:
                    return datetime.strptime(s.split('+')[0], '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    return s

    def clean_description(self):
        """
        """
        # clean Description
        self.check_validity(self.description, 'description')

    def clean_jobid(self):
        """
        """
        # clean JobId
        self.check_validity(self.jobid, 'jobid')

    def clean_job_title(self):
        """
        """
        # clean JobTitle
        self.check_validity(self.job_title, 'job_title')

    def clean_type_role(self):
        """
        """
        self.check_validity(self.type_role, 'type_role')

    def clean_subject_area(self):
        """
        """
        self.check_validity(self.subject_area, 'subject_area')

    def clean_location(self):
        """
        """
        self.check_validity(self.location, 'location')

    def clean_hours(self):
        """
        """
        self.check_validity(self.hours, 'hours')

    def clean_place_on(self):
        """
        """
        self.check_validity(self.placed_on, 'placed_on')
        self.placed_on = self.transform_valid_date(self.remove_suffix_date(self.placed_on))
        if isinstance(self.placed_on, str):
            self.add_invalid_code('placed_on')

    def clean_closes(self):
        """
        """
        self.check_validity(self.closes, 'closes')
        self.closes = self.transform_valid_date(self.remove_suffix_date(self.closes))
        if isinstance(self.closes, str):
            self.add_invalid_code('closes')

    def add_duration(self):
        """
        Add a duration of the job ads by substracting closes to placed_on
        """
        if 'placed_on' not in self.invalid_code and 'closes' not in self.invalid_code:
            try:
                duration_ad = self.closes - self.placed_on
                self.duration_ad_days = duration_ad.days
            except (AttributeError, TypeError):
                pass

    def clean_employRef(self):
        """
        """
        self.check_validity(self.employRef, 'EmployRef')

    def clean_employer(self):
        """
        """
        self.check_validity(self.employer, 'employer')

    def clean_type_role(self):
        """
        """
        self.check_validity(self.employer, 'type_role')

    def clean_contract(self):
        """
        """
        # clean Contract
        self.check_validity(self.contract, 'contract')
        try:
            if self.Contract == 'Contract / Temporary':
                self.Contract = 'Temporary'
            elif self.Contract == 'Permanent':
                self.Contract = 'Permanent'
            elif self.Contract == 'Fixed-Term/Contract':
                self.Contract = 'Fixed-Term'
            else:
                self.add_invalid_code("contract")
        except AttributeError:
            pass

    def clean_salary(self, field, fieldname):
        """
        """
        self.check_validity(field, fieldname)
        try:
            # First remove all the white spaces and replace them with a single whitespace
            field = ' '.join(field.split())
            # Are there numbers associated with a £ symbol in the format £nn,nnn or £nnn,nnn?
            salary_fields = re.findall(r'£[0-9]?[0-9][0-9],[0-9][0-9][0-9]', field,
                                       flags=re.MULTILINE)
            num_salary_fields = len(salary_fields)
            if num_salary_fields == 0:
                # Does the salary field contain only text, i.e. no numbers
                if re.search(r'[0-9]', field):
                    self.add_invalid_code(fieldname)

            elif num_salary_fields > 2:
                self.add_invalid_code(fieldname)
            else:
                # extract numeric salary values
                salary_values = []
                for salary_field in salary_fields:
                    # remove characters '£, ' from salary_field, e.g. '£37,394 '
                    salary_value = int(salary_field.translate(str.maketrans('', '', '£, ')))
                    salary_values.append(salary_value)
                salary_values.sort()
                # Is the smallest number < £11k?
                salary_min = salary_values[0]
                if salary_min < 8000:
                    self.add_invalid_code(fieldname)
                else:
                    # One number or two numbers?
                    if len(salary_values) == 1:
                        self.salary_min = salary_values[0]
                        self.salary_max = salary_values[0]
                    elif len(salary_values) == 2:
                        self.salary_min = salary_values[0]
                        self.salary_max = salary_values[1]
                    # When there is three records is because the third salary
                    # is for potential progression in the future
                    elif len(salary_values) == 3:
                        self.salary_min = salary_values[0]
                        self.salary_max = salary_values[1]
                    else:
                        self.add_invalid_code(fieldname)
        except TypeError:
            pass

    def check_validity(self, *args):
        """
        Adds the passed invalid code to the output invalid_codes field.
        :param: invalid_code: the invalid code to add
        """
        if args[0] is None:
            return self.set_up_invalidity(*args)  # return to stop the func() here
        if isinstance(args[0], str):
            if args[0].strip().lower() in ['', 'not specified']:
                self.set_up_invalidity(*args)

    def set_up_invalidity(self, *args):
        """
        Function to remove the attribute if exists
        add the code into the list
        :params: args[0] attribute args[1] key
        """
        self.add_invalid_code(args[1])
        # self.remove_key(args[1])

    def add_invalid_code(self, key):
        """
        Check the attribute of invalid code and append a key
        :params: a string to append to the self.invalid_code dictionary
        """
        try:
            self.invalid_code.append(key)
        except AttributeError:
            self.invalid_code = [key]

    def check_match(self, element_to_compare, list_to_use, limit_ratio=0.70):
        """
        Check if the element to compare is close enough to an element
        in the list provided
        """
        ratio_list = list()
        for s in list_to_use:
            # Get the ratio for each entry and the self.employer value
            ratio = difflib.SequenceMatcher(None, element_to_compare, s).ratio()
            ratio_list.append((s, ratio))
            # If ratio is == 1 it means it is a perfect match
            if ratio == 1:
                break

        # get the maximum ratio[1] in the list and return the associated tuple
        best_match = max(ratio_list, key=itemgetter(1))
        if best_match[1] >= limit_ratio:
            return best_match[0]
        else:
            return None

    def add_uk_university(self):
        """
        Check the string from employer if it matches an UK university
        provided by the file self.uk_uni_list using difflib
        """
        if hasattr(self, 'employer'):

            # clean the employer string to get only key word
            employer = self.text_cleaner.clean_text(self.employer.split('-')[0])
            # List of keyword that are associated to university
            list_uni = ['university', 'school', 'college']
            if len(set(employer).intersection(set(list_uni))) > 0:
                self.uk_university = self.employer
                return

            # if did not match an university. Try to match with the list provided
            employer = ' '.join(set([x for x in employer]))
            best_match = self.check_match(employer, self.uk_uni_list)
            if best_match:
                self.uk_university = best_match

    def add_in_uk(self):
        """
        Check the string from extra_location is from uk
        """
        if hasattr(self, 'extra_location'):
            if self.extra_location in ['Northern England',
                                       'London Midlands of England Scotland',
                                       'South West England',
                                       'South East England',
                                       'Wales',
                                       'Republic of Ireland',
                                       'Northern Ireland']:
                self.in_uk = True

    def add_postcode(self):
        """
        If there is a uk_university, try to match it with the code
        provided by self.dict_uk_uni_postcode
        """
        if hasattr(self, 'uk_university'):
            best_match = self.check_match(self.uk_university, self.uk_postcode_dict.keys())
            if best_match:
                self.uk_postcode = self.uk_postcode_dict[best_match]

    def add_median_salary(self):
        """
        If there is a salary_min and salary_max, create a SalaryMedian which is the middle
        between the two salary. to get an average
        """
        if hasattr(self, 'salary_min') and hasattr(self, 'salary_max'):
            self.salary_median = self.salary_min + ((self.salary_max - self.salary_min)/ 2)

    def add_not_student(self):
        """
        Check if the jobs ads does not contain `PhD` or `Master` in the type role
        If it does, return false
        """
        if hasattr(self, 'type_role'):
            try:
                for i in self.type_role:
                    if i.lower().rstrip() in ['phd', 'masters']:
                        return
                self.not_student = True
                return
            except TypeError:  # Empty type_role
                return

        self.not_student = False

    def clean_row(self):
        self.clean_description()
        self.clean_jobid()
        self.clean_job_title()
        # New enhanced content (check in november 2017) doesnt have that key
        # self.clean_type_role()
        # New enhanced content (check in november 2017) doesnt have that key
        # self.clean_location_region()
        self.clean_location()
        self.clean_hours()
        self.clean_place_on()
        self.clean_closes()
        self.clean_contract()
        self.clean_type_role()
        self.add_duration()
        # self.add_uk_university()
        # self.add_in_uk()
        # self.add_postcode()
        self.clean_salary(self.salary, 'salary')
        self.clean_salary(self.funding_amount, 'funding_amount')
        if hasattr(self, 'funding_amount') and 'contract' in self.invalid_code:
            self.invalid_code.remove('contract')
            self.contract = 'funding'

        if hasattr(self, 'salary_max') or hasattr(self, 'salary_min'):
            try:
                self.invalid_code.remove('salary')
            except ValueError:
                pass
            try:
                self.invalid_code.remove('funding_amount')
            except ValueError:
                pass

        self.clean_employer()
        if self.invalid_code == []:
            del self.invalid_code
        try:
            if 'funding_amount' in self.invalid_code:
                self.invalid_code.remove('funding_amount')
                if 'salary' in self.invalid_code:
                    pass
                else:
                    self.invalid_code.append('salary')
        except AttributeError:
            pass
        # New enhanced content (check in november 2017) doesnt have that key
        # Which was a reference to the employer (in form of MED203221)
        # commented
        # self.clean_employRef()
        self.clean_subject_area()
        self.add_median_salary()
        # self.add_not_student()

    def to_dictionary(self):
        """
        Converts this output row to a dictionary of key: value pairs.
        :return: a dictionary of key: value pairs
        """
        result = dict()
        # Check the list of key set up in TransformKey() and append
        # the keys created during the analysis
        # for k in [k for k in self.input_row.keys()] + self.new_keys:
        for k in self.keys_to_record:
            try:
                result[k] = getattr(self, k)
            except AttributeError:
                pass

        return result


def main():
    """
    """
    pass


if __name__ == '__main__':
    main()
