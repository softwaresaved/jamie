#!/usr/bin/env python
# encoding: utf-8

import sys
import json
import bs4
import copy
import string
import calendar
import datetime
import datefinder
from pathlib import Path
from contextlib import suppress  # alternative to try: (...) except Exception: pass
from typing import Union
from .clean import OutputRow

_table_punc = bytes.maketrans(
    str.encode(string.punctuation), b" " * len(string.punctuation)
)
_table_space = bytes.maketrans(bytes(" ", "utf-8"), bytes("_", "utf-8"))
MINIMUM_DESCRIPTION_LENGTH = 150  # characters

# Maximum number of days a job can be advertised, ensures that
# incorrectly parsed dates are not too far in the future
JOB_ADVERTISING_DURATION_DAYS = 400


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

    EPOCH_YEAR = 2014  # Earliest year for datefinder fuzzy matching

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
        self.enhanced = self._soup.find("div", {"id": "enhanced-content"}) is not None
        self.data["enhanced"] = self.enhanced

    def _first_section(self, elem, attrs):
        return self._soup.findAll(elem, attrs)[0].get_text(separator=u" ")

    def _tag_text(self, tag):
        "Returns text in tag if found, otherwise returns None"
        found = self._soup.find(tag)
        return found.text if found else None

    @staticmethod
    def transform_key(key_string):
        "Create slug of key for insertion into dictionary"
        key_string = str.encode(key_string.lower(), "utf-8").translate(_table_punc)
        return (
            key_string.translate(_table_space)
            .decode("utf-8")
            .replace("_", " ")
            .rstrip()
            .replace(" ", "_")
        )

    @property
    def employer(self):
        _employer = None
        try:
            _employer = self._soup.find("h3").text
        except AttributeError:
            with suppress(AttributeError, TypeError):
                for emp in self._soup.find("a").get("href"):
                    if emp[:10] == "/employer/":
                        _employer = emp[:10]
        return _employer

    @property
    def job_title(self):
        return self._tag_text("h1")

    @property
    def place(self):
        return self._tag_text("h3")

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
            for fmt in [
                ("div", {"class": "section", "id": None}),
                ("div", {"id": "enhanced-right"}),
                ("div", {"id": "enhanced-content"}),
            ]:
                with suppress(IndexError):
                    return self._first_section(*fmt)
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
                    if description.name == "p" and not text_desc:
                        text_desc = True
                    if text_desc:
                        description_text.append(description.text)
                return " ".join(description_text)
            with suppress(AttributeError):
                jobPost = self._soup.find("div", {"class": "jobPost"})
                if jobPost:
                    paras = [p.get_text(separator=u" ") for p in jobPost.findAll("p")]
                    if len(paras) > 3:
                        # First para is location and salary, second is usually about working hours
                        return "\n".join(
                            p
                            for p in paras[2:-1]
                            if len(p) > MINIMUM_DESCRIPTION_LENGTH
                        )
            with suppress(AttributeError):
                paras = [p.get_text(separator=u" ") for p in self._soup.findAll("p")]
                # Only keep long paragraphs and ones without emails
                # (usually contact information)
                return "\n".join(
                    p
                    for p in paras
                    if len(p) > MINIMUM_DESCRIPTION_LENGTH and "@" not in p
                )

    def _extra_details_items(self, section):
        key = section.find("p")
        if key is None:
            return None
        original_content = key.findNext("p")
        return (
            "extra_" + self.transform_key(key.text),
            (
                # Sometime the content is not within a tag <p> and within
                # <a> tag but under a <div class='j-nav-pill-box'> tags
                # Check if the previous one give results and if not try to
                # parse the <div> tag Work for <p>Subject Area(s) don't
                # know for the others
                [el.text for el in original_content.findAll("a")]
                or [el.text for el in section.findNext("div").findAll("a")]
                or original_content.text
            ),
        )

    def extra_details(self):
        "Get the extra details at the end of description"
        if not self.enhanced:
            return dict(
                filter(
                    None,
                    map(
                        self._extra_details_items,
                        self._soup.findAll("div", {"class": "inlineBox"}),
                    ),
                )
            )
        else:
            return {
                self.transform_key(element.text): element.findNext("td").text
                for element in self._soup.findAll("td", {"class": "detail-heading"})
            }

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
        self.data.update(self.extra_details())
        return self.data

    def _extract_json_ads(self):
        "Get the json content from the page and return a dictionary from it"
        content_json = self._soup.find("script", attrs={"type": "application/ld+json"})
        with suppress(AttributeError):
            return json.loads(content_json.contents[0])

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
        tag = self._soup.find("input", {"class": "j-form-input__location"})
        if tag:
            return tag["value"]

    @property
    def new_type_role(self):

        type_role = self._soup.find(
            lambda tag: tag.name == "b" and "Type / Role:" in tag.text
        )
        if type_role is not None:
            list_type_role = []
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
        "Parse JSON data in HTML body"
        for k, v in {
            "name": "json.title",
            "employer": "json.hiringOrganization.name",
            "department": "json.hiringOrganization.department.name",
            "salary": "json.baseSalary.value",
            "placed_on": "json.datePosted",
            "closes": "json.validThrough",
            "description": "json.description",
            "type_role": "json.employmentType",
        }.items():
            self.data[k] = self._get_nested_data(v)
        self.data["description"] = bs4.BeautifulSoup(
            self.data["description"], "html.parser"
        ).get_text()
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
            }
        )
        return self.data

    @staticmethod
    def _earliest_date_in_text(text):
        with suppress(calendar.IllegalMonthError, TypeError):
            return min(
                [
                    d
                    for d in datefinder.find_dates(text.replace(":", ""))
                    if d.year >= JobFile.EPOCH_YEAR
                ],
                default=None,
            )

    def parse(self, clean=True):
        "Parses job HTML or JSON and returns as a dictionary"
        raw_json = self._extract_json_ads()
        max_date = datetime.datetime.now() + datetime.timedelta(
            days=JOB_ADVERTISING_DURATION_DAYS
        )
        if raw_json:
            self.data["json"] = raw_json
            self.parse_json()
        else:
            self.parse_html()
        if clean:
            self.data = OutputRow(self.data).clean_row().to_dictionary()
        # Pick the first non-null option for date
        date = (
            self.data.get("placed_on", None)
            or self.data.get("closes", None)
            or self._earliest_date_in_text(self._soup.get_text())
        )
        if date and date < max_date:
            self.data["date"] = date

        return self

    @property
    def json(self):
        _json = self.data.copy()
        for date in ["placed_on", "closes", "date"]:
            if date in self.data and isinstance(self.data[date], datetime.datetime):
                _json[date] = self.data[date].date().isoformat()
        return _json


def main(filename):
    print(json.dumps(JobFile(filename).parse().json, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
