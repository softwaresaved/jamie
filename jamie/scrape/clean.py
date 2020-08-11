"""
This Python 3 script cleans an input jobs dictionary and outputs a cleaned jobs dictionary.
"""

import re
import difflib
from operator import itemgetter
from contextlib import suppress
import dateutil.parser
from ..data import employers
from ..clean_text import clean_text


class OutputRow:
    """
    A class that receive a dictionary as input. It checks several keys and operate additional
    cleaning operation. When the target keys are not present or the content is wrong, a list of error
    is generated and recorded.
    Return the cleaned dictionary and the key with the invalid code with it
    """

    def __init__(self, input_row, employer="uk_uni"):
        """
        *Create attributes from the dict() input_row
        *Import the transformKey __init__() to have access to the key list
        * Transform the key of the input_row to the defined ones in TransformKey
        * Create a list of new key to add after cleaning process
        """
        # Create attribute from the input_row
        self.input_row = input_row
        self._employer = employer

        self.needed_keys = [
            "jobid",
            "description",
            "job_title",
            "employer",
            "location",
            "salary",
            "funding_amount",
            "hours",
            "contract",
            "placed_on",
            "closes",
            "subject_area",
        ]

        # Create a list of keys that are added during the cleaning process
        self.new_keys = [
            "invalid_code",
            "salary_min",
            "salary_max",
            "duration_ad_days",
            "uk_university",
            "uk_postcode",
            "salary_median",
            "not_student",
            "in_uk",
        ]
        # Create a list for all the keys that are going to be recorded in the database
        # populate it with the new_keys and the first
        self.keys_to_record = self.new_keys
        self.create_dictionary()
        self.invalid_code = set()

    @staticmethod
    def strip_if_string(s):
        "Returns string trimmed of whitespace, for other datatypes this is no-op"
        if isinstance(s, str):
            return s.strip()
        else:
            return s

    @staticmethod
    def parse_date(date):
        "Parses date from job attributes"
        try:
            return dateutil.parser.parse(
                date, dayfirst=True, fuzzy=False, ignoretz=True
            )
        except dateutil.parser._parser.ParserError:
            return None

    def read_uni_list_file(self):
        """
        Read the txt file containing all universities from a text file
        and create a set of strings
        """
        return set(
            " ".join(set([x for x in clean_text(empl)]))
            for empl in employers[self._employer]["list"]
        )

    def read_postcode(self):
        """
        Read the csv file containing university and postcode for UK only
        """
        return {
            row.PROVIDER_NAME: row.POSTCODE
            for row in employers[self._employer]["postcodes"].itertuples()
        }

    def matching_key(self, key):
        """
        Check if a key match a better name
        """
        key = key.rstrip().lower()

        return {
            "contract_type": "contract",
            "contract": "contract",
            "contract type": "contract",
            "expires": "closes",
            "closes": "closes",
            "closing_date": "closes",
            "placed on": "placed_on",
            "name": "job_title",
            "type___role": "type_role",
            "extra_type___role": "type_role",
            "subject_area_s": "subject_area",
            "subject_area": "subject_area",
            "extra_subject_area": "subject_area",
            "extra_subject_area_s": "subject_area",
            "location_s": "location",
            "location": "location",
            "extra_location_s": "extra_location",
        }.get(key, key)

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

        # Ensure all needed keys are present
        for key in self.needed_keys:
            if not hasattr(self, key):
                setattr(self, key, "")

    def clean_date(self, key):
        "Cleans a date field, and updates invalid code"
        self.check_validity_key(key)
        setattr(self, key, OutputRow.parse_date(getattr(self, key)))
        if getattr(self, key) is None:
            self.invalid_code.add(key)

    def clean_closes(self):
        self.check_validity(self.closes, "closes")
        self.closes = OutputRow.parse_date(self.closes)
        if self.closes is None:
            self.invalid_code.add("closes")

    def add_duration(self):
        """
        Add a duration of the job ads by substracting closes to placed_on
        """
        if not {"placed_on", "closes"} & self.invalid_code:
            with suppress(AttributeError, TypeError):
                duration_ad = self.closes - self.placed_on
                self.duration_ad_days = duration_ad.days

    def clean_employRef(self):
        self.check_validity(self.employRef, "EmployRef")

    def clean_salary(self, field, fieldname):
        """
        """
        self.check_validity(field, fieldname)
        with suppress(TypeError):
            # First remove all the white spaces and replace them with a single whitespace
            field = " ".join(field.split())
            # Are there numbers associated with a £ symbol in the format £nn,nnn or £nnn,nnn?
            salary_fields = re.findall(
                r"£[0-9]?[0-9][0-9],[0-9][0-9][0-9]", field, flags=re.MULTILINE
            )
            num_salary_fields = len(salary_fields)
            if num_salary_fields == 0:
                # Does the salary field contain only text, i.e. no numbers
                if re.search(r"[0-9]", field):
                    self.invalid_code.add(fieldname)

            elif num_salary_fields > 2:
                self.invalid_code.add(fieldname)
            else:
                # extract numeric salary values
                salary_values = []
                for salary_field in salary_fields:
                    # remove characters '£, ' from salary_field, e.g. '£37,394 '
                    salary_value = int(
                        salary_field.translate(str.maketrans("", "", "£, "))
                    )
                    salary_values.append(salary_value)
                salary_values.sort()
                # Is the smallest number < £11k?
                salary_min = salary_values[0]
                if salary_min < 8000:
                    self.invalid_code.add(fieldname)
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
                        # Check that the other salary value is actually
                        # higher
                        assert self.salary_values[2] > self.salary_values[1]
                    else:
                        self.invalid_code.add(fieldname)

    def check_validity(self, value, key):
        "Checks if value is valid, otherwise updates invalid_code"
        if value is None or (
            isinstance(value, str) and value.strip().lower() in ["", "not specified"]
        ):
            self.invalid_code.add(key)

    def check_validity_key(self, key):
        """Checks if self.key is valid, otherwise adds key to invalid code.
        Wrapper around check_validity, with value set to self.key"""
        return self.check_validity(getattr(self, key), key)

    def check_match(self, element_to_compare, list_to_use, limit_ratio=0.70):
        """
        Check if the element to compare is close enough to an element
        in the list provided
        """
        ratio_list = []
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
        if hasattr(self, "employer"):

            # clean the employer string to get only key word
            employer = clean_text(self.employer.split("-")[0])
            # List of keyword that are associated to university
            list_uni = ["university", "school", "college"]
            if set(employer) & set(list_uni):
                self.uk_university = self.employer
                return

            # if did not match an university. Try to match with the list provided
            employer = " ".join(set(employer))
            best_match = self.check_match(employer, self.uk_uni_list)
            if best_match:
                self.uk_university = best_match

    def add_in_uk(self):
        """
        Check the string from extra_location is from uk
        """
        if hasattr(self, "extra_location") and self.extra_location in [
            "Northern England",
            "London Midlands of England Scotland",
            "South West England",
            "South East England",
            "Wales",
            "Republic of Ireland",
            "Northern Ireland",
        ]:
            self.in_uk = True

    def add_postcode(self):
        """
        If there is a uk_university, try to match it with the code
        provided by self.dict_uk_uni_postcode
        """
        if hasattr(self, "uk_university"):
            best_match = self.check_match(
                self.uk_university, self.uk_postcode_dict.keys()
            )
            if best_match:
                self.uk_postcode = self.uk_postcode_dict[best_match]

    def add_median_salary(self):
        """
        If there is a salary_min and salary_max, create a SalaryMedian which is the middle
        between the two salary. to get an average
        """
        if hasattr(self, "salary_min") and hasattr(self, "salary_max"):
            self.salary_median = (self.salary_min + self.salary_max) / 2

    def add_not_student(self):
        """
        Check if the jobs ads does not contain `PhD` or `Master` in the type role
        If it does, return false
        """
        if hasattr(self, "type_role"):
            try:
                for i in self.type_role:
                    if i.lower().rstrip() in ["phd", "masters"]:
                        return
                self.not_student = True
                return
            except TypeError:  # Empty type_role
                return

        self.not_student = False

    def clean_row(self):
        for key in [
            "contract",
            "description",
            "employer",
            "hours",
            "job_title",
            "jobid",
            "location",
            "subject_area",
        ]:
            self.check_validity_key(key)
        self.clean_date("placed_on")
        self.clean_date("closes")
        self.check_validity(self.employer, "type_role")
        self.add_duration()
        self.clean_salary(self.salary, "salary")
        self.clean_salary(self.funding_amount, "funding_amount")
        if hasattr(self, "funding_amount") and "contract" in self.invalid_code:
            self.invalid_code -= {"contract"}
            self.contract = "funding"

        if hasattr(self, "salary_max") or hasattr(self, "salary_min"):
            self.invalid_code -= {"salary"}
            self.invalid_code -= {"funding_amount"}

        if "funding_amount" in self.invalid_code:
            self.invalid_code -= {"funding_amount"}
            self.invalid_code.add("salary")

        self.add_median_salary()
        if self.invalid_code == set():
            del self.invalid_code
        else:
            self.invalid_code = sorted(self.invalid_code)
        return self

    def to_dictionary(self):
        """
        Converts this output row to a dictionary of key: value pairs.
        :return: a dictionary of key: value pairs
        """
        return {
            k: OutputRow.strip_if_string(getattr(self, k))
            for k in self.keys_to_record
            if hasattr(self, k)
        }
