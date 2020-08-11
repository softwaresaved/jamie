#!/usr/bin/env python
# encoding: utf-8

import sys
import json
import bs4
import copy
import string
import datetime
from pathlib import Path
from contextlib import suppress  # alternative to try: (...) except Exception: pass
from typing import Union
from .clean import OutputRow

_table_punc = bytes.maketrans(
    str.encode(string.punctuation), b" " * len(string.punctuation)
)
_table_space = bytes.maketrans(bytes(" ", "utf-8"), bytes("_", "utf-8"))
MINIMUM_DESCRIPTION_LENGTH = 150  # characters


def get_nested_key(d, key):
    keys = key.split(".")
    o = copy.deepcopy(d)
    with suppress(KeyError):
        for k in keys:
            o = o[k]
        return o


class JobFile:
    """
    Represents a single jobs.ac.uk scraped document

    Parameters
    ----------
    content : Path or str
        If type Path, filename of jobs.ac.uk scraped document, or if str,
        the content itself
    jobid : Optional[str]
        If specified, used as jobid. When reading from a Path, the filename
        is used instead to create the jobid. When reading from a string,
        jobid is not optional.
    """

    def __init__(self, content: Union[Path, str], jobid: str = None):
        self.data = {}
        if isinstance(content, Path):
            self.filename = content
            self._content = self.filename.read_text()
            self.data["filename"] = str(self.filename)
            # Assign jobid if specified, otherwise take it from filename
            self.data["jobid"] = jobid or self.filename.stem
        elif isinstance(content, str):
            if jobid is None:
                raise ValueError("jobid can't be None if content is string")
            self._content = content
        else:
            raise ValueError("content must be one of Path or str")
        self._soup = bs4.BeautifulSoup(self._content, "html.parser")

        # Enhanced content alters behaviour of some parsing
        if self._soup.find("div", {"id": "enhanced-content"}):
            self.enhanced = True
        else:
            self.enhanced = False
        self.data["enhanced"] = self.enhanced

    def _first_section(self, elem, attrs):
        return self._soup.findAll(elem, attrs)[0].get_text(separator=u" ")

    @staticmethod
    def transform_key(key_string):
        "Create slug of key for insertion into dictionary"
        key_string = key_string.lower()
        key_string = str.encode(key_string, "utf-8").translate(_table_punc)
        key_string = key_string.translate(_table_space)
        key_string = key_string.decode("utf-8")
        key_string = key_string.replace("_", " ")
        key_string = key_string.rstrip()
        key_string = key_string.replace(" ", "_")
        return key_string

    @property
    def employer(self):
        _employer = None
        try:
            _employer = self._soup.find("h3").text
        except AttributeError:
            try:
                for emp in self._soup.find("a").get("href"):
                    if emp[:10] == "/employer/":
                        _employer = emp[:10]
            except (AttributeError, TypeError):
                pass
        return _employer

    @property
    def job_title(self):
        with suppress(AttributeError):
            return self._soup.find("h1").text

    @property
    def place(self):
        with suppress(AttributeError):
            return self._soup.find("h3").text

    def _details_group(
        self, tag, tag_value=None, condition=None,
    ):
        """Return job details corresponding to a specific format

        Parameters
        ----------
        tag : str
            Tag for the job attribute field. A class restriction can be
            specified by using "tag.class" such as "td.detail-heading"
        tag_value : str, optional
            Tag for the job attribute value field. If set to None, uses nextSibling
        condition : lambda, optional
            An optional filter function to apply on the element before inclusion

        Returns
        -------
        dict
            Job details dictionary corresponding to the given format
        """
        if "." in tag:
            tag, tag_class = tag.split(".")
        else:
            tag_class = None
        class_filter = {"class": tag_class} if tag_class else {}
        if condition is None:
            condition = lambda x: True  # NOQA
        if tag_value is None:
            with suppress(AttributeError):
                return {
                    self.transform_key(el.text): el.nextSibling.get_text()
                    for el in self._soup.findAll(tag, class_filter)
                    if condition(el)
                }
            with suppress(AttributeError):
                # Sometimes, next sibling is directly a text
                return {
                    self.transform_key(el.text): str(el.nextSibling)
                    for el in self._soup.findAll(tag, class_filter)
                    if condition(el)
                }
        else:
            with suppress(AttributeError):
                return {
                    self.transform_key(el.text): el.findNext(tag_value).text
                    for el in self._soup.findAll(tag, class_filter)
                    if condition(el)
                }

    def details(self):
        "Return job details as dictionary"

        # Loop through the various formats in which job details are
        # presented and return the first matching format
        for fmt in [
            ("td.detail-heading", "td"),
            ("th.j-advert-details__table-header", "td"),
            ("dt", "dd"),
            ("strong", None, lambda x: len(x.get_text()) < 30 and ":" in x.get_text()),
        ]:
            _details = self._details_group(*fmt)
            if _details:
                return _details
        return {}

    @property
    def description(self):
        # To add space when encounter <p> and <br> tags otherwise words are
        # attached
        # Some ads have the first div as <div id='enhanced-content'> which
        # change the structure of the html
        if self.enhanced:
            with suppress(IndexError):
                return self._first_section("div", {"class": "section", "id": None})
            with suppress(IndexError):
                return self._first_section("div", {"id": "enhanced-right"})
            try:
                return self._first_section("div", {"id": "enhanced-content"})
            except IndexError:
                print(self._soup)
                raise
        else:
            with suppress(IndexError):
                sections = [
                    s.get_text(separator=u" ")
                    for s in self._soup.findAll("div", {"class": "section", "id": None})
                ]
                sections.sort(key=len)
                if len(sections[-1]) > MINIMUM_DESCRIPTION_LENGTH:
                    return sections[-1]
            with suppress(IndexError):
                return self._first_section("div", {"id": "job-description"})
            with suppress(IndexError):
                return self._first_section("div", {"id": "rightcol"})
            with suppress(AttributeError):
                description_text = []
                section = self._soup.find("div", {"class": "col-lg-12"})
                # Need to find the first <p>. The description is under that one
                # but also contains differents tags
                text_desc = False
                for description in section.findAll():
                    if description.name == "p" and text_desc is False:
                        text_desc = True
                    if text_desc is True:
                        description_text.append(description.text)
                return " ".join(description_text)
            with suppress(AttributeError):
                jobPost = self._soup.find("div", {"class": "jobPost"})
                if jobPost:
                    paras = [p.get_text(separator=u" ") for p in jobPost.findAll("p")]
                    if len(paras) > 3:
                        paras = paras[
                            2:-1
                        ]  # first para is location and salary, second is usually about working hours
                        paras = [
                            p for p in paras if len(p) > MINIMUM_DESCRIPTION_LENGTH
                        ]
                        return "\n".join(paras)
            with suppress(AttributeError):
                paras = [p.get_text(separator=u" ") for p in self._soup.findAll("p")]
                # Only keep long paragraphs and ones without emails
                # (usually contact information)
                return "\n".join(
                    [
                        p
                        for p in paras
                        if len(p) > MINIMUM_DESCRIPTION_LENGTH and "@" not in p
                    ]
                )

    def extra_details(self):
        "Get the extra details at the end of description"
        if not self.enhanced:
            for section in self._soup.findAll("div", {"class": "inlineBox"}):
                key = section.find("p")
                if key:
                    original_content = key.findNext("p")
                    key = JobFile.transform_key(key.text)
                    result = list()
                    for element in original_content.findAll("a"):
                        result.append(element.text)
                    # Sometime the content is not within a tag <p> and
                    # within <a> tag but under a
                    # <div class='j-nav-pill-box'> tags
                    # Check if the previous one give results and if not
                    # try to parse the <div> tag
                    # Work for <p>Subject Area(s) don't know for the others
                    if len(result) == 0:
                        second_content = section.findNext("div")
                        for element in second_content.findAll("a"):
                            result.append(element.text)
                        if len(result) == 0:
                            result = original_content.text
                    yield {"extra_{}".format(key): result}
        else:
            for element in self._soup.findAll("td", {"class": "detail-heading"}):
                key = element.text
                key = JobFile.transform_key(key)
                content = element.findNext("td")
                content = content.text
                yield {key: content}

    def parse_html(self):
        self.data.update(
            {
                "description": self.description,
                "employer": self.employer,
                "name": self.job_title,
                "location": self.place,
            }
        )
        self.data.update(self.details())

        for extra_details in self.extra_details():
            self.data.update(extra_details)
        return self.data

    def _extract_json_ads(self):
        "Get the json content from the page and return a dictionary from it"
        content_json = self._soup.find("script", attrs={"type": "application/ld+json"})
        try:
            content_json = content_json.contents[0]
            return json.loads(content_json)
        except AttributeError:
            return None

    @property
    def new_subject_area(self):
        subject = self._soup.find(
            lambda tag: tag.name == "b" and "Subject Area(s):" in tag.text
        )
        if subject is not None:
            list_subject = []
            while True:
                # find the next subject which not contain the value but it is just before
                # the input that does have the value
                subject = subject.findNext("input", attrs={"name": "categoryId[]"})
                try:
                    list_subject.append(subject.findNext("input")["value"])
                except AttributeError:  # means it is the end of the list
                    break
            return list_subject

    @property
    def new_extra_location(self):
        for tag in self._soup.find_all(
            "input", attrs={"class": "j-form-input__location"}
        ):
            return tag["value"]

    @property
    def new_type_role(self):

        type_role = self._soup.find(
            lambda tag: tag.name == "b" and "Type / Role:" in tag.text
        )
        if type_role is not None:
            list_type_role = list()
            while True:
                # find the next type_role which not contain the value but it is just before
                # the input that does have the value
                type_role = type_role.findNext("input", attrs={"name": "jobTypeId[]"})
                try:
                    list_type_role.append(type_role.findNext("input")["value"])
                except AttributeError:  # means it is the end of the list
                    break
            return list_type_role

    def _get_nested_data(self, keys):
        return get_nested_key(self.data, keys)

    def parse_json(self):
        """
        """
        for k, v in {
            "name": "json.title",
            "employer": "json.hiringOrganization.name",
            "department": "json.hiringOrganization.department.name",
            "salary": "json.baseSalary.value",
            "placed_on": "json.datePosted",
            "closes": "json.validThrough",
            "description": "json.description",
            "region": "json.jobLocation.address.addressRegion",
        }.items():
            self.data[k] = self._get_nested_data(v)
        joblocation = self._get_nested_data("json.jobLocation")
        if isinstance(joblocation, list):
            joblocation = joblocation[0]
        self.data["location"] = get_nested_key(joblocation, "address.addressLocality")
        self.data["region"] = get_nested_key(joblocation, "address.addressRegion")
        hours_contract = get_nested_key(self.data, "json.employmentType")
        if hours_contract:
            splitted = hours_contract.split(",")
            # The hours and the contract are stored in the same k:v
            # Sometime when part time and full time are both available, the first
            # two elements are them. The last one is always the contract
            self.data["hours"] = splitted[:-1]
            self.data["contract"] = splitted[-1]
        self.data.update(
            {
                "enhanced": "json",
                "subject_area": self.new_subject_area,
                "extra_location": self.new_extra_location,
                "type_role": self.type_role,
            }
        )
        return self.data

    def parse(self, clean=True):
        "Parses job HTML or JSON and returns as a dictionary"
        raw_json = self._extract_json_ads()
        if raw_json:
            self.data["json"] = raw_json
            self.parse_json()
        else:
            self.parse_html()
        if clean:
            self.data = OutputRow(self.data).clean_row().to_dictionary()
        return self

    @property
    def json(self):
        _json = self.data.copy()
        for date in ["placed_on", "closes"]:
            if date in self.data and isinstance(self.data[date], datetime.datetime):
                _json[date] = self.data[date].date().isoformat()
        return _json


def main(filename):
    print(json.dumps(JobFile(filename).parse().json, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
