"""
Spending analysis and comparative tools
"""

import re
import numpy as np
import pandas as pd
from nrel_p3.utilities import filter, employee_id_regex


class Analysis:
    """Analyze pricing tool estimate versus worday report."""

    def __init__(self, pt_estimate, wd_report):
        """
        Parameters
        ----------
        pt_estimate : nrel_p3.pricing_tool.Estimate
            Initialized pricing tool Estimate object.
        wd_report : nrel_p3.workday_report.Report
            Initialized workday report object
        """
        self.pt_estimate = pt_estimate
        self.wd_report = wd_report

    def get_spend_table(self, filters=None):
        """Get a timeseries spend table for the whole project, one charge code,
        or by person

        Parameters
        ----------
        filters : dict | None
            Set of filters where keys are columns in the pt_estimate and
            wd_report data and values are one or more items to sub select in
            the column. For example,
            ``filters={'charge_code': '12765.07.01.01', 'eid': '19864'}``
            will return data for a single charge code for a single person.

        Returns
        -------
        df : pd.DataFrame
            Timeseries cost table with columns: 'Year-Month', 'planned_cost',
            'planned_cost_cumulative', 'actual_cost', 'actual_cost_cumulative'
        """

        pt_df = self.pt_estimate.plan(filters)
        wd_df = self.wd_report.actuals(filters)
        df = pt_df.join(wd_df, how='outer').reset_index()
        return df

    def get_worker_spend(self, filters=None):
        """Get a timeseries spend table with worker breakdowns.

        Parameters
        ----------
        filters : dict | None
            Set of filters where keys are columns in the pt_estimate and
            wd_report data and values are one or more items to sub select in
            the column. For example,
            ``filters={'charge_code': '12765.07.01.01'}``
            will return data for a single charge code

        Returns
        -------
        df : pd.DataFrame
            Timeseries cost table with columns: 'Year-Month', 'planned_cost',
            'planned_cost_cumulative', 'actual_cost', 'actual_cost_cumulative',
            'eid', 'worker'
        """

        if filters is None:
            filters = {}

        df = []
        for eid, worker in self.wd_report.eid_map.items():
            filters['eid'] = eid
            pt_df = self.pt_estimate.plan(filters)
            wd_df = self.wd_report.actuals(filters)
            idf = pt_df.join(wd_df, how='outer')
            idf['eid'] = eid
            idf['worker'] = worker
            idf = idf.reset_index()
            df.append(idf)

        df = pd.concat(df, axis=0, ignore_index=True)
        return df
