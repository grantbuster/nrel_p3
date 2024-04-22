"""
Interface for workday reports
"""
import glob
import re
import numpy as np
import pandas as pd
from nrel_p3.utilities import filter, employee_id_regex


class Report:
    """Interface for workday task number reports

    To export report from workday, search the following:
        "Task Number Report for Task Managers - Not Grouped"

    Then enter a conservative start date and end date, enter your charge code
    of interest, and then press OK. In the top right you should see an option
    to expor the result to Excel.

    To automatically create a report on a preset schedule, navigate the
    following flow:

    Workday -> Menu -> Reports -> Tools -> Schedule a Report -> By Report Type
    -> Custom Reports -> Task Number Report for Task Managers - Not Grouped

    Then select Run Frequency = "Weekly Recurrence", do not check "Populate
    Default Prompt Values", then press OK.

    Finally, fill out the Report Criteria, Schedule, and Output to fit your
    preferences and press OK.

    """

    def __init__(self, fp_xlsx):
        """
        Parameters
        ----------
        fp_xlsx : str
            Filepath to NREL workday export from the following report:
            "Task Number Report for Task Managers - Not Grouped".
            Can also be a list of these reports or a string with a wild*card
            for multiple reports (one for each charge code)
        """

        if isinstance(fp_xlsx, str):
            fp_xlsx = glob.glob(fp_xlsx)

        self.data = []
        for fp in fp_xlsx:
            self.data.append(pd.read_excel(fp))

        self.data = pd.concat(self.data, ignore_index=True)

        date_time = pd.to_datetime(self.data['Time Entered Date'])
        year = date_time.dt.year.astype(str)
        month = date_time.dt.month.astype(str)
        cc = self.data['Reported Project Plan Task']
        cc = cc.apply(self.charge_code_regex)

        self.data['charge_code'] = cc
        self.data['eid'] = self.data['Worker'].apply(employee_id_regex)
        self.data['Time Entered Date'] = date_time
        self.data['Year-Month'] = year + '-' + month.str.zfill(2)

    def __repr__(self):
        return self.data.__repr__()

    def __str__(self):
        return str(self.data)

    @staticmethod
    def charge_code_regex(text):
        """Get the charge code "12765.07.01.01" from text if the charge code is
        in the format: "- > 12765 - 07.01.01-Topic 5.1 Downscalin (Starts: ..)"

        Returns
        -------
        out : str | None
            Charge code string or None if not found
        """
        pattern = r'(\d+)\s*-\s*(\d+\.\d+\.\d+)'
        match = re.search(pattern, text)
        extracted = None

        if match:
            extracted = f"{match.group(1)} - {match.group(2)}"
            extracted = extracted.replace(' - ', '.')

        return extracted

    @property
    def worker_map(self):
        """Get a dictionary mapping {worker_name: employee_id}"""
        worker_list = list(self.data['Worker'])
        eid_list = list(self.data['eid'])
        workers = {worker: eid for worker, eid in zip(worker_list, eid_list)}
        return workers

    @property
    def eid_map(self):
        """Get a dictionary mapping {employee_id: worker_name}"""
        worker_list = list(self.data['Worker'])
        eid_list = list(self.data['eid'])
        eids = {eid: worker for worker, eid in zip(worker_list, eid_list)}
        return eids

    def add_rates(self, rates):
        """Workday tables only have hours charged by default. Take in a rates
        table from the pricing tool to calculate actual costs.

        Parameters
        ----------
        rates : dict | pd.Series
            Input labor rates here either from
            nrel_p3.pricing_tool.Estimate.rates or with a custom dict, e.g.,
            {'NEW_SLR': 100}
        """

        for i, row in self.data.iterrows():
            slr = row['SLR']
            rate = np.nan
            if slr in rates:
                rate = rates[slr]
                cost = row['Total Hours (Time Tracking)'] * rate
                self.data.at[i, 'cost'] = cost

    @property
    def missing_rates(self):
        """Get a list of SLR names that are missing their rates
        (cost per hour). Use ``add_rates()`` to add these rates to estimate
        labor costs."""
        missing_cost = np.isnan(self.data['cost'])
        missing_rates = list(self.data.loc[missing_cost, 'SLR'].unique())
        return missing_rates

    def actuals(self, filters=None):
        """Run the calculation of actual charges through time

        Parameters
        ----------
        filters : dict | None
            Set of filters where keys are columns in the workday report file
            and values are one or more items to sub select in the column. For
            example,
            ``filters={'charge_code': '12765.07.01.01', 'eid': '19864'}``
            will return data for a single charge code for a single person.

        Returns
        -------
        actuals : pd.DataFrame
            An aggregated version of the workday actuals table with Year-Month
            index and columns: actual_cost, actual_cost_cumulative
        """

        if filters is not None:
            subdf = filter(self.data, filters)
        else:
            subdf = self.data.copy()

        actuals = subdf.groupby('Year-Month')[['cost']].sum()
        actuals['actual_cost_cumulative'] = actuals['cost'].cumsum()
        actuals = actuals.rename({'cost': 'actual_cost'}, axis=1)
        return actuals
