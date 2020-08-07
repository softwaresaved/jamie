# Custom types and enums for use in Jamie
import json
from bson.json_util import loads
import datetime
from enum import Enum, auto
from box import Box
from typing import Optional, List
from dataclasses import dataclass, asdict


class Alert(Enum):
    "Alert levels for reporting"
    High = Box(
        {
            "alert_level": "alert-success",
            "text": "High confidence is defined to be above a score of 0.80",
        }
    )
    Medium = Box(
        {
            "alert_level": "alert-warning",
            "text": "Medium confidence is defined to be for scores from 0.60 to 0.80",
        }
    )
    Low = Box(
        {
            "alert_level": "alert-danger",
            "text": "Low confidence is defined for a score below 0.60",
        }
    )

    @staticmethod
    def level(n):
        if n > 0.80:
            return Alert.High
        elif n > 0.60:
            return Alert.Medium
        else:
            return Alert.Low


class PrecisionRecall(Enum):

    High = """Both precision and recall are high. The model captures most
of the target job type as well as being precise and avoiding false
negatives. The reported estimates can be considered a good estimate for the
target job type."""

    Low = """Both precision and recall are low or average. The model can neither
correctly classify most of the positives, nor is it precise. The reported estimates
are unreliable for the target job type."""

    HighLow = """Precision is high while recall is low or average. The model is
conservative; the target job type is precisely identified with few
false positives, but in doing so, the model fails to identify many
jobs. The reported estimates should be considered an underestimate for
the target job type."""

    LowHigh = """"Precision is low or average while recall is high. The model is
overpredicting, that is predicting more jobs in the target job type than
actual, thus leading to low precision; while recall is high because of
the overprediction. The reported estimates should be considered an overestimate
for the target job type."""

    @staticmethod
    def get(precision, recall):
        return_map = {
            (True, True): PrecisionRecall.High,
            (False, False): PrecisionRecall.Low,
            (True, False): PrecisionRecall.HighLow,
            (False, True): PrecisionRecall.LowHigh,
        }
        return return_map[precision == Alert.High, recall == Alert.High]


class Contract(Enum):
    "Contract type: Fixed Term or Permanent"
    FixedTerm = auto()
    Permanent = auto()


class JobType(Enum):
    rse = {
        "title": "Research Software Engineer",
        "search_keywords": ["research", "software"],
    }

    @property
    def title(self):
        return self.value["title"]

    @property
    def search_keywords(self):
        return self.value["search_keywords"]


@dataclass
class JobPrediction:
    """Represents prediction for a single job

    Attributes
    ----------
    jobid : str
        JobID from jobs.ac.uk
    job_title : str
        Job title
    snapshot : str
        Model snapshot used for prediction
    closes : datetime.date
        Close date for job
    contract : Contract
        Contract type
    department : str
        Department of the academic institution that
        the job is associated with
    employer : str
        Job employer
    posted : datetime.date
        Date job was posted
    extra_location : str
        Broad geographical location of job position
    salary_min : Optional[int]
        Minimum salary associated with the job. Sometimes
        jobs have a range of salaries depending on the experience
        of the applicant.
    salary_max : Optional[int]
        Maximum salary associated with the job. Sometimes
        jobs have a range of salaries depending on the experience
        of the applicant.
    salary_median : Optional[int]
        Median salary associated with the job.
    probability : float
        Probability that the job is classified in the positive class
    probability_lower : float
        Lower confidence interval of the probability
    probability_upper : float
        Upper confidence interval of the probability

    Parameters
    ----------
    prediction : dict
        Dictionary representing a single prediction from the JSONL file
        generated by :class:`Predict`
    """

    jobid: str
    snapshot: str
    contract: str
    employer: str
    hours: List[str]
    job_title: str
    posted: datetime.date
    extra_location: str
    probability: float
    probability_lower: float
    probability_upper: float
    department: Optional[str] = None
    location: Optional[str] = None
    salary_max: Optional[float] = None
    salary_min: Optional[float] = None
    salary_median: Optional[float] = None

    def __init__(self, prediction):
        self.jobid = prediction["jobid"]
        self.snapshot = prediction["snapshot"]
        if "contract" in prediction:
            self.contract = (
                Contract.Permanent
                if prediction["contract"] == "Permanent"
                else Contract.FixedTerm
            )
        else:
            self.contract = None
        self.employer = prediction.get("employer", None)
        self.hours = prediction.get("hours", None)
        self.job_title = prediction["job_title"]
        self.department = prediction.get("department", None)
        self.location = prediction.get("location", None)
        self.extra_location = prediction.get("extra_location", None)
        self.salary_max = prediction.get("salary_max", None)
        self.salary_min = prediction.get("salary_min", None)
        self.salary_median = prediction.get("salary_median", None)
        for p in ["probability", "lower_ci", "upper_ci"]:
            if not 0 <= prediction[p] <= 1:
                raise ValueError(
                    "Tried reading invalid {}={}.".format(p, prediction[p])
                )
        self.probability = prediction["probability"]
        self.probability_lower = prediction["lower_ci"]
        self.probability_upper = prediction["upper_ci"]
        if "placed_on" in prediction:
            self.posted = loads(json.dumps(prediction["placed_on"])).date()
        else:
            self.posted = None

    def to_dict(self):
        return asdict(self)
