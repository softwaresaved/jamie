"""

This Python 3 script cleans an input jobs dictionary and outputs a cleaned jobs dictionary.


"""

import re
import difflib
from operator import itemgetter
from datetime import datetime


class OutputRow:
    """
    A class that receive a dictionary as input. It checks several keys and operate additional
    cleaning operation. When the target keys are not present or the content is wrong, a list of error
    is generated and recorded.
    Return the cleaned dictionary and the key with the invalid code with it
    """

    def __init__(self, input_row):
        """
        *Create attributes from the dict() input_row
        *Import the transformKey __init__() to have access to the key list
        *Set up the default value of include_in_study as True
        * Transform the key of the input_row to the defined ones in TransformKey
        * Create a list of new key to add after cleaning process
        """
        # Create attribute from the input_row
        self.input_row = input_row

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
                            'closes']


        # Create a list of keys that are added during the cleaning process
        self.new_keys = ['include_in_study',
                         'invalid_code',
                         'salary_min',
                         'salary_max',
                         'duration_ad_days',
                         'uk_university']
        # Create a list for all the keys that are going to be recorded in the database
        # populate it with the new_keys and the first
        self.keys_to_record = list(self.new_keys)
        self.create_dictionary()
        # Set attribute include_in_study as True by default
        # This attribute is changed when some invalid codes
        # are found
        self.include_in_study = True
        self.invalid_code = list()
        # get the list of university from the file ./uk_uni_list.txt for the method
        # self.add_uk_university
        self.uk_uni_list = self.read_uni_list_file()

    def read_uni_list_file(self):
        """
        Read the txt file containing all universities from a text file
        and create a set of strings
        """
        set_uni_list = set()
        with open('./data/uk_uni_list.txt', 'r') as f:
            for l in f:
                set_uni_list.add(l.strip())
        return set_uni_list

    def matching_key(self, key):
        """
        Check if a key match a better name
        """
        if key == 'contract_type' or key == 'contract' or key == 'contract type':
            key = 'contract'
        elif key == 'expires' or key == 'closes':
            key = 'closes'
        elif key == 'placed on':
            key = 'placed_on'
        elif key == 'name':
            key = 'job_title'
        if key == 'type___role':
            key = 'type_role'
        elif key == 'subject_area_s' or key == 'subject_area':
            key = 'subject_area'
        elif key == 'location_s' or key == 'location':
            key = 'location'
        return key

    def create_dictionary(self):
        """
        Parse the input_row and set up the attribute of
        the object with the key value
        When it finisheds set up the keys from self.needed_keys
        that are not present to empty string
        for the invalid_code
        """
        # Create the attribute based on input_row dict()
        del self.input_row['raw_content']
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

    def clean_location_region(self):
        """
        """
        # clean LocationRegion
        self.check_validity(self.LocationRegion, 'LocationRegion')
        # Process if the self.LocationRegion is not empty
        # Check if the location is within UK
        if self.LocationRegion not in ('Midlands of England',
                                       'South East England',
                                       'London',
                                       'Northern England',
                                       'South West England',
                                       'Scotland',
                                       'Wales',
                                       'Northern Ireland'):
            self.add_invalid_code("LocationRegion")

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
                        self.SalaryMin = salary_values[0]
                        self.SalaryMax = salary_values[0]
                    elif len(salary_values) == 2:
                        self.SalaryMin = salary_values[0]
                        self.SalaryMax = salary_values[1]
                    # When there is three records is because the third salary
                    # is for potential progression in the future
                    elif len(salary_values) == 3:
                        self.SalaryMin = salary_values[0]
                        self.SalaryMax = salary_values[1]
                    else:
                        self.add_invalid_code(fieldname)
        except TypeError:
            pass

    def check_validity(self, *args):
        """
        Adds the passed invalid code to the output invalid_codes field.
        Sets the output include_in_study field to "invalid".
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
        set up the self.include_in_study to False
        :params: a string to append to the self.invalid_code dictionary
        """
        try:
            self.invalid_code.append(key)
        except AttributeError:
            self.invalid_code = [key]
        self.include_in_study = False

    def add_uk_university(self):
        """
        Check the string from employer if it matches an UK university
        provided by the file self.uk_uni_list using difflib
        """
        if hasattr(self, 'employer'):
            # Break the employer string and lower it while removinge white spac

            employer = self.employer.split('-')[0].split('–')[0].strip().lower()
            # Parse the entry from the self.uk_uni_list

            ratio_list = list()
            for s in self.uk_uni_list:
                to_match = s.lower().strip()

                # Get the ratio for each entry and the self.employer value
                ratio = difflib.SequenceMatcher(None, employer, to_match).ratio()
                ratio_list.append((s, ratio))
                # If ratio is == 1 it means it is a perfect match
                if ratio == 1:
                    break

            # get the maximum ratio[1] in the list and return the associated tuple
            best_match = max(ratio_list, key=itemgetter(1))
            # Arbitrary limit of confidence for considering the two strings as a match
            if best_match[1] >= 0.90:
                self.uk_university = best_match[0]

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
        self.add_duration()
        self.add_uk_university()
        self.clean_salary(self.salary, 'salary')
        self.clean_salary(self.funding_amount, 'funding_amount')
        if hasattr(self, 'funding_amount') and 'contract' in self.invalid_code:
            self.invalid_code.remove('contract')
            self.contract = 'funding'

        if hasattr(self, 'SalaryMax') or hasattr(self, 'SalaryMin'):
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
        # self.clean_subject_area()

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
    Running for test purpose
    """
    file_to_parse = '../../../outputs/uniqueValue/salary.csv'
    print('Reading: {}'.format(file_to_parse))
    result = dict()
    with open(file_to_parse, 'r') as f:
        for l in f:

            l = ' '.join(l.split())
            # salary_fields = re.findall(r'£[0-9]?[0-9][0-9],[0-9][0-9][0-9](?: |$)', l,
            salary_fields = re.findall(r'£[0-9]?[0-9][0-9],[0-9][0-9][0-9]', l,
                                                flags=re.MULTILINE)
            result[len(salary_fields)] = result.get(len(salary_fields), 0)+1
            size = len(salary_fields)
            if size == 1:
                print(l)
                print(salary_fields)
    for k in result:
        print(k, result[k])


if __name__ == '__main__':
    main()
