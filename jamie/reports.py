"""Generate reports from :class:`PredictionSnapshot`"""
import chevron
import calendar
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from shutil import copyfile
from .snapshots import ReportSnapshot

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
        self.data = self.prediction_snapshot.data
        # Drop jobs without salary information
        self.data = self.data[~pd.isna(self.data.salary_median)]
        # Convert to datetime format to allow pandas operations
        self.data['posted'] = pd.DatetimeIndex(self.data.posted)
        # Drop PhD jobs, this should ideally be done earlier
        self.data = self.data[~self.data.job_title.str.contains("PhD")]

    @staticmethod
    def metrics(df):
        "Return summary metrics for prediction snapshot data"
        return {
            'total': len(df),
            'npos': len(df[df.probability > 0.5]),
            'proportion_pos': len(df[df.probability > 0.5]) / len(df),
            'npos_lower': len(df[df.probability_upper > 0.5]),
            'npos_upper': len(df[df.probability_lower > 0.5]),
            'salary_mean': df[~pd.isna(df.salary_median)].salary_median.mean(),
            'salary_mean_pos': df[(~pd.isna(df.salary_median)) &
                                  (df.probability > 0.5)].salary_median.mean()
        }

    @property
    def by_month(self):
        "Returns pd.DataFrame having data grouped by month"
        if self._monthly is None:
            self._monthly = pd.DataFrame({'group': i, **self.metrics(data)} for i, data
                                         in self.data.groupby(self.data.posted.dt.month))
        return self._monthly

    @property
    def by_year(self):
        "Returns pd.DataFrame having data grouped by year"
        if self._yearly is None:
            self._yearly = pd.DataFrame({'group': i, **self.metrics(data)} for i, data
                                        in self.data.groupby(self.data.posted.dt.year))
        return self._yearly

    def _graph_njobs(self, df, fn, monthly):
        plt.clf()
        fig, ax = plt.subplots()
        xax = "month" if monthly else "group"
        if monthly:   # months
            df['month'] = df.group.map(lambda x: calendar.month_name[x][:3])
        ax.plot(df[xax], df.npos)
        ax.fill_between(df[xax], df.npos_lower, df.npos_upper, color='b', alpha=.1)
        plt.savefig(self.snapshot.path / fn)

    def _graph_propjobs(self, df, fn, monthly):
        plt.clf()
        plt.ylim(0, 1)
        if monthly:
            df['month'] = df.group.map(lambda x: calendar.month_name[x][:3])
            plt.plot(df['month'], df.proportion_pos)
        else:
            plt.plot(df.group, df.proportion_pos)
        plt.savefig(self.snapshot.path / fn)

    def _graph_salary_mean(self):
        plt.clf()
        df = self.by_year
        print(df)
        plt.plot(df.group, df.salary_mean_pos)
        plt.savefig(self.snapshot.path / "mean_salary.png")

    def _graph_njobs_yearly(self):
        self._graph_njobs(self.by_year, "njobs_yearly.png", monthly=False)

    def _graph_njobs_monthly(self):
        self._graph_njobs(self.by_month, "njobs_monthly.png", monthly=True)

    def _graph_propjobs_yearly(self):
        self._graph_propjobs(self.by_year, "propjobs_yearly.png", monthly=False)

    def _graph_propjobs_monthly(self):
        self._graph_propjobs(self.by_month, "propjobs_monthly.png", monthly=True)

    def make_graphs(self):
        self._graph_njobs_yearly()
        self._graph_njobs_monthly()
        self._graph_propjobs_yearly()
        self._graph_propjobs_monthly()
        self._graph_salary_mean()

    def create(self):
        "Create a report and store in a report snapshot"
        self.make_graphs()
        templates = Path(__file__).parent / 'templates'
        copyfile(templates / 'style.css', self.snapshot.path / 'style.css')
        copyfile(templates / 'bootstrap.min.css', self.snapshot.path / 'bootstrap.min.css')
        data = {
            "date": self.snapshot.name,
            "njobs_year_fig": "njobs_yearly.png",
            "propjobs_year_fig": "propjobs_yearly.png",
            "njobs_month_fig": "njobs_monthly.png",
            "propjobs_month_fig": "propjobs_monthly.png",
            "mean_salary_fig": "mean_salary.png"
        }
        with (templates / 'default_index.mustache').open() as fp:
            (self.snapshot.path / "index.html").write_text(chevron.render(fp, data))
