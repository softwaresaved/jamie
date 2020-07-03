"""Generate reports from :class:`PredictionSnapshot`"""
import json
import chevron
import calendar
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from shutil import copyfile
from .logger import logger
from .snapshots import ReportSnapshot
from .types import Confidence, JobType

logger = logger(name="report", stream_level="DEBUG")

def label(x):
    # "2017-01-01" -> "Jan 2017"
    year, month, _ = x.split("-")
    return calendar.month_name[int(float(month))][:3] + " " + year

def fix_day(date, day="01"):
    if date is not None:
        yyyy, mm, _ = str(date).split("-")
        return "-".join([yyyy, mm, day])
    else:
        return None

class Report:
    """Report generator

    Parameters
    ----------
    prediction_snapshot : :class:`PredictionSnapshot`
        Prediction snapshot to use for report generation
    """
    _monthly = None
    _yearly = None

    def __init__(self, prediction_snapshot):
        self.prediction_snapshot = prediction_snapshot
        self.snapshot = ReportSnapshot(self.prediction_snapshot.name).create()
        self.featureset = self.prediction_snapshot.metadata['training']['featureset']
        self.data = self.prediction_snapshot.data

        logger.info("              Total number of jobs: %d", len(self.data))
        # Drop jobs without salary information
        self.data = self.data[~pd.isna(self.data.salary_median)]
        logger.info("After dropping jobs without salary: %d", len(self.data))

        # Drop jobs without posted date
        self.data = self.data[~pd.isna(self.data.posted)]
        logger.info("After dropping jobs without posted: %d", len(self.data))
        self.data['year_month'] = self.data.posted.apply(fix_day)

        # Convert to datetime format to allow pandas operations
        self.data['posted'] = pd.DatetimeIndex(self.data.posted)
        # Drop PhD jobs, this should ideally be done earlier
        self.data = self.data[~self.data.job_title.str.contains("PhD")]
        logger.info("  After dropping jobs at PhD level: %d", len(self.data))
        # job_title_match contains True or False depending on whether the
        # job_title contained the target job type
        # (such as "Research Software Engineer")
        self.data['job_title_match'] = self.data.job_title.str.contains(
            JobType[self.featureset].value, case=False)

    @staticmethod
    def metrics(df):
        "Return summary metrics for prediction snapshot data"
        salary = df[(~pd.isna(df.salary_median)) & (df.probability > 0.5)]
        return {
            'total': len(df),
            'npos': len(df[df.probability > 0.5]),
            'proportion_pos': len(df[df.probability > 0.5]) / len(df),
            'njob_match': int(df.job_title_match.sum()),
            'npos_lower': len(df[df.probability_upper > 0.5]),
            'npos_upper': len(df[df.probability_lower > 0.5]),
            'salary_mean': df.salary_median.mean(skipna=True),
            'salary_mean_pos': None if salary.empty else salary.salary_median.mean()
        }

    def by_month(self, as_dataframe=True):
        "Returns list of dicts or dataframe having data grouped by month"
        if self._monthly is None:
            self._monthly = [{'group': i, **self.metrics(data)} for i, data
                             in self.data.groupby(self.data.year_month)]
        return pd.DataFrame(self._monthly) if as_dataframe else self._monthly

    def by_year(self, as_dataframe=True):
        "Returns list of dicts or dataframe having data grouped by year"
        if self._yearly is None:
            self._yearly = [{'group': i, **self.metrics(data)} for i, data
                            in self.data.groupby(self.data.posted.dt.year)]
        return pd.DataFrame(self._yearly) if as_dataframe else self._yearly

    def _graph_njobs(self, df, fn, monthly):
        plt.clf()
        fig, ax = plt.subplots()
        xax = "label_month" if monthly else "group"
        if monthly:   # months
            df['label_month'] = df.group.map(label)
        ax.plot(df[xax], df.npos)
        ax.fill_between(df[xax], df.npos_lower, df.npos_upper, color='b', alpha=.1)
        plt.savefig(self.snapshot.path / fn)

    def _graph_propjobs(self, df, fn, monthly):
        plt.clf()
        plt.ylim(0, 1)

        if monthly:
            df['label_month'] = df.group.map(label)
            plt.plot(df['label_month'], df.proportion_pos)
        else:
            plt.plot(df.group, df.proportion_pos)
        plt.savefig(self.snapshot.path / fn)

    def _graph_salary_mean(self):
        plt.clf()
        df = self.by_year()
        print(df)
        plt.plot(df.group, df.salary_mean_pos)
        plt.savefig(self.snapshot.path / "mean_salary.png")

    def _graph_njobs_yearly(self):
        self._graph_njobs(self.by_year(), "njobs_yearly.png", monthly=False)

    def _graph_njobs_monthly(self):
        self._graph_njobs(self.by_month(), "njobs_monthly.png", monthly=True)

    def _graph_propjobs_yearly(self):
        self._graph_propjobs(self.by_year(), "propjobs_yearly.png", monthly=False)

    def _graph_propjobs_monthly(self):
        self._graph_propjobs(self.by_month(), "propjobs_monthly.png", monthly=True)

    def make_graphs(self):
        self._graph_njobs_yearly()
        self._graph_njobs_monthly()
        self._graph_propjobs_yearly()
        self._graph_propjobs_monthly()
        self._graph_salary_mean()

    def create(self):
        "Create a report and store in a report snapshot"
        self.make_graphs()
        score = self.prediction_snapshot.metadata['best_model_average_score']
        confidence = Confidence.level(score)
        templates = Path(__file__).parent / 'templates'
        with (self.snapshot.path / "by_year.json").open("w") as fp:
            json.dump(self.by_year(as_dataframe=False), fp, indent=2, sort_keys=True)
        with (self.snapshot.path / "by_month.json").open("w") as fp:
            json.dump(self.by_month(as_dataframe=False), fp, indent=2, sort_keys=True)
        copyfile(templates / 'script.js', self.snapshot.path / 'script.js')
        data = {
            "job_type": JobType[self.featureset].value,
            "alert_level": confidence.value.alert_level,
            "confidence": confidence.name,
            "confidence_text": confidence.value.text,
            "score_value": "{:.2f}".format(score),
            "score_type": self.prediction_snapshot.metadata['training']['scoring'],
            "date": self.snapshot.name,
            "njobs_year_fig": "njobs_yearly.png",
            "propjobs_year_fig": "propjobs_yearly.png",
            "njobs_month_fig": "njobs_monthly.png",
            "propjobs_month_fig": "propjobs_monthly.png",
            "mean_salary_fig": "mean_salary.png"
        }
        with (templates / 'default_index.mustache').open() as fp:
            (self.snapshot.path / "index.html").write_text(chevron.render(fp, data))
