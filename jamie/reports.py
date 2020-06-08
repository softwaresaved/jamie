"""Generate reports from :class:`PredictionSnapshot`"""
import pandas as pd
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
        self.report_snapshot = ReportSnapshot(self.prediction_snapshot.name).create()
        self._monthly = self.monthly()
        self._yearly = self.yearly()

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
        df = self.prediction_snapshot.data
        if self._monthly is None:
            self._monthly = pd.DataFrame({'group': i, **self.metrics(data)} for i, data
                                         in df.groupby(df.posted.dt.month))
        return self._monthly

    @property
    def by_year(self):
        "Returns pd.DataFrame having data grouped by year"
        df = self.prediction_snapshot.data
        if self._yearly is None:
            self._yearly = pd.DataFrame({'group': i, **self.metrics(data)} for i, data
                                        in df.groupby(df.posted.dt.year))
        return self._yearly

    def _graph_njobs_yearly(self):
        pass

    def _graph_njobs_monthly(self):
        pass

    def _graph_propjobs_yearly(self):
        pass

    def _graph_propjobs_monthly(self):
        pass

    def _graph_salary_mean_yearly(self):
        pass
