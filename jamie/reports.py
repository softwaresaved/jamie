"""Generate reports from :class:`PredictionSnapshot`"""
import json
import chevron
import calendar
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from shutil import copyfile
from .lib import fail
from .logger import logger
from .snapshots import ReportSnapshot, ModelSnapshot, TrainingSnapshot
from .types import Alert, JobType, PrecisionRecall, Contract

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


def slugify_location(x):
    return "nloc_" + x.replace("&", "").replace(",", "").lower().replace(" ", "_")


class Report:
    """Report generator

    Parameters
    ----------
    prediction_snapshot : :class:`PredictionSnapshot`
        Prediction snapshot to use for report generation
    """

    _monthly = None
    _yearly = None
    _training_monthly = None

    def __init__(self, prediction_snapshot):
        self.prediction_snapshot = prediction_snapshot
        self.training_data = TrainingSnapshot(
            self.prediction_snapshot.metadata["training"]["training_snapshot"]
        ).data
        self.training_data["year_month"] = self.training_data.placed_on.apply(fix_day)
        self.snapshot = ReportSnapshot(self.prediction_snapshot.name).create()
        model_snapshot = ModelSnapshot(self.prediction_snapshot.metadata["snapshot"])
        if not model_snapshot.exists():
            fail("Model snapshot '{}' does not exist".format(model_snapshot.name))

        self.scores = model_snapshot.data["scores"]
        self.scoring = self.prediction_snapshot.metadata["training"]["scoring"]
        # Keep only the best score classifier as a dictionary
        self.scores = (
            self.scores.sort_values("mean_" + self.scoring, ascending=False)
            .head(1)
            .to_dict("records")[0]
        )
        self.featureset = self.prediction_snapshot.metadata["training"]["featureset"]
        self.data = self.prediction_snapshot.data

        logger.info("              Total number of jobs: %d", len(self.data))
        # Drop jobs without salary information
        self.data = self.data[~pd.isna(self.data.salary_median)]
        logger.info("After dropping jobs without salary: %d", len(self.data))

        # Drop jobs without posted date
        self.data = self.data[~pd.isna(self.data.posted)]
        logger.info("After dropping jobs without posted: %d", len(self.data))
        self.data["year_month"] = self.data.posted.apply(fix_day)

        # Convert to datetime format to allow pandas operations
        self.data["posted"] = pd.DatetimeIndex(self.data.posted)
        # Drop PhD jobs, this should ideally be done earlier
        self.data = self.data[~self.data.job_title.str.contains("PhD")]
        logger.info("  After dropping jobs at PhD level: %d", len(self.data))
        # job_title_match contains True or False depending on whether the
        # job_title contained the target job type keywords
        # (such as containing both 'research' and 'software')
        self.data["job_title_match"] = np.logical_and.reduce(
            [
                self.data.job_title.str.contains(keyword, case=False)
                for keyword in JobType[self.featureset].search_keywords
            ]
        )

    @staticmethod
    def metrics(df):
        "Return summary metrics for prediction snapshot data"
        salary = df[(~pd.isna(df.salary_median)) & (df.probability > 0.5)]
        npos = int((df.probability > 0.5).sum())
        ncontract_permanent = int(
            ((df.contract == Contract.Permanent) & (df.probability > 0.5)).sum()
        )
        ncontract_fixed_term = int(
            ((df.contract == Contract.FixedTerm) & (df.probability > 0.5)).sum()
        )
        locations = {
            slugify_location(loc): int(
                ((df.probability > 0.5) & (df.extra_location == loc)).sum()
            )
            for loc in [
                "Africa",
                "All Locations",
                "Asia & Middle East",
                "Europe",
                "London",
                "Midlands of England",
                "North, South & Central America",
                "Northern England",
                "Northern Ireland",
                "Republic of Ireland",
                "Scotland",
                "South East England",
                "South West England",
                "Wales",
            ]
        }
        return {
            "total": len(df),
            "npos": npos,
            "proportion_pos": npos / len(df),
            "njob_match": int(df.job_title_match.sum()),
            "npos_lower": int((df.probability_upper > 0.5).sum()),
            "npos_upper": int((df.probability_lower > 0.5).sum()),
            "ncontract_permanent": ncontract_permanent,
            "ncontract_fixed_term": ncontract_fixed_term,
            "propcontract_permanent": ncontract_permanent / npos if npos > 0 else 0,
            "propcontract_fixed_term": ncontract_fixed_term / npos if npos > 0 else 0,
            "salary_mean": df.salary_median.mean(skipna=True),
            "salary_mean_pos": None if salary.empty else salary.salary_median.mean(),
            **locations,
        }

    @staticmethod
    def training_metrics(
        df, label="aggregate_tags", positive_label=1, negative_label=0
    ):
        "Return summary metrics for training snapshot"
        return {
            "total": len(df),
            "npos": int((df[label] == positive_label).sum()),
            "nneg": int((df[label] == negative_label).sum()),
            "nphd": int((df.job_title.str.contains("PhD")).sum()),
            "nnotphd": int((~df.job_title.str.contains("PhD")).sum()),
            "proportion_pos": (df[label] == positive_label).sum() / len(df),
        }

    def training_by_month(self, as_dataframe=False):
        "Returns list of dicts or dataframe having training data grouped by month"
        if self._training_monthly is None:
            self._training_monthly = [
                {"group": i, **self.training_metrics(data)}
                for i, data in self.training_data.groupby(self.training_data.year_month)
            ]
        return (
            pd.DataFrame(self._training_monthly)
            if as_dataframe
            else self._training_monthly
        )

    def by_month(self, as_dataframe=False):
        "Returns list of dicts or dataframe having data grouped by month"
        if self._monthly is None:
            self._monthly = [
                {"group": i, **self.metrics(data)}
                for i, data in self.data.groupby(self.data.year_month)
            ]
        return pd.DataFrame(self._monthly) if as_dataframe else self._monthly

    def by_year(self, as_dataframe=False):
        "Returns list of dicts or dataframe having data grouped by year"
        if self._yearly is None:
            self._yearly = [
                {"group": str(i), **self.metrics(data)}
                for i, data in self.data.groupby(self.data.posted.dt.year)
            ]
        return pd.DataFrame(self._yearly) if as_dataframe else self._yearly

    def _graph_njobs(self, df, fn, monthly):
        plt.clf()
        fig, ax = plt.subplots()
        xax = "label_month" if monthly else "group"
        if monthly:  # months
            df["label_month"] = df.group.map(label)
        ax.plot(df[xax], df.npos)
        ax.fill_between(df[xax], df.npos_lower, df.npos_upper, color="b", alpha=0.1)
        plt.savefig(self.snapshot.path / fn)

    def _graph_propjobs(self, df, fn, monthly):
        plt.clf()
        plt.ylim(0, 1)

        if monthly:
            df["label_month"] = df.group.map(label)
            plt.plot(df["label_month"], df.proportion_pos)
        else:
            plt.plot(df.group, df.proportion_pos)
        plt.savefig(self.snapshot.path / fn)

    def _graph_salary_mean(self):
        plt.clf()
        df = self.by_year(as_dataframe=True)
        plt.plot(df.group, df.salary_mean_pos)
        plt.savefig(self.snapshot.path / "mean_salary.png")

    def _graph_njobs_yearly(self):
        self._graph_njobs(
            self.by_year(as_dataframe=True), "njobs_yearly.png", monthly=False
        )

    def _graph_njobs_monthly(self):
        self._graph_njobs(
            self.by_month(as_dataframe=True), "njobs_monthly.png", monthly=True
        )

    def _graph_propjobs_yearly(self):
        self._graph_propjobs(
            self.by_year(as_dataframe=True), "propjobs_yearly.png", monthly=False
        )

    def _graph_propjobs_monthly(self):
        self._graph_propjobs(
            self.by_month(as_dataframe=True), "propjobs_monthly.png", monthly=True
        )

    def make_graphs(self):
        self._graph_njobs_yearly()
        self._graph_njobs_monthly()
        self._graph_propjobs_yearly()
        self._graph_propjobs_monthly()
        self._graph_salary_mean()

    def create(self):
        "Create a report and store in a report snapshot"
        self.make_graphs()
        score = self.prediction_snapshot.metadata["best_model_average_score"]
        alert = Alert.level(score)
        recall = self.scores["mean_recall"]
        recall_alert = Alert.level(recall)
        templates = Path(__file__).parent / "templates"
        per_job_target = (
            100
            * int(self.data.job_title_match.sum())
            / int((self.data.probability > 0.5).sum())
        )
        with (self.snapshot.path / "by_year.json").open("w") as fp:
            json.dump(self.by_year(), fp, indent=2, sort_keys=True)
        with (self.snapshot.path / "by_month.json").open("w") as fp:
            json.dump(self.by_month(), fp, indent=2, sort_keys=True)
        with (self.snapshot.path / "training_by_month.json").open("w") as fp:
            json.dump(self.training_by_month(), fp, indent=2, sort_keys=True)
        copyfile(templates / "script.js", self.snapshot.path / "script.js")
        copyfile(templates / "style.css", self.snapshot.path / "style.css")
        data = {
            "mean_salary_target": "{:,.0f}".format(
                self.data[self.data.probability > 0.5].salary_median.mean()
            ),
            "mean_salary_non_target": "{:,.0f}".format(
                self.data[self.data.probability <= 0.5].salary_median.mean()
            ),
            "job_target_keywords": ", ".join(JobType[self.featureset].search_keywords),
            "per_job_target": "{:.1f}".format(per_job_target),
            "job_type": JobType[self.featureset].title,
            "alert_level": alert.value["alert_level"],
            "score_name": self.scoring.replace("-", " ").capitalize(),
            "score_level": alert.name,
            "score": "{:.4f}".format(score),
            "score_explanation": PrecisionRecall.get(alert, recall_alert).value,
            "recall_alert_level": recall_alert.value["alert_level"],
            "recall_level": recall_alert.name,
            "recall": "{:.4f}".format(recall),
            "date": self.snapshot.name,
            "njobs_year_fig": "njobs_yearly.png",
            "propjobs_year_fig": "propjobs_yearly.png",
            "njobs_month_fig": "njobs_monthly.png",
            "propjobs_month_fig": "propjobs_monthly.png",
            "mean_salary_fig": "mean_salary.png",
        }
        with (templates / "default_index.mustache").open() as fp:
            (self.snapshot.path / "index.html").write_text(chevron.render(fp, data))
        return self
