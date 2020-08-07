import pytest
from jamie.scrape.process import get_nested_key

d = {
    "json": {
        "datePosted": "2020-04-12",
        "hiringOrganization": {"department": {"name": "computer_science"}},
        "jobLocation": {"address": {"addressRegion": "England"}},
        "description": "Another job description here",
    },
    "base": True,
}


@pytest.mark.parametrize(
    "key,value",
    [
        ("json.datePosted", "2020-04-12"),
        ("json.hiringOrganization.department.name", "computer_science"),
        ("json.jobLocation.address.addressRegion", "England"),
        ("json.description", "Another job description here"),
        ("base", True),
    ],
)
def test_get_nested_key(key, value):
    assert get_nested_key(d, key) == value
