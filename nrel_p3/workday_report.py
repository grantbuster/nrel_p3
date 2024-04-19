"""
Interface for workday reports
"""

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
        """
        self.data = pd.read_excel(fp_xlsx)

        date_time = pd.to_datetime(self.data['Time Entered Date'])
        year = date_time.dt.year.astype(str)
        month = date_time.dt.month.astype(str)
        cc = self.data['Reported Project Plan Task']
        cc = cc.apply(self.charge_code_regex)

        self.data['charge_code'] = cc
        self.data['eid'] = self.data['Worker'].apply(employee_id_regex)
        self.data['Time Entered Date'] = date_time
        self.data['Year-Month'] = year + '-' + month.str.zfill(2)

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

    def add_costs(self, rates, extra=None):
        """Workday tables only have hours charged by default. Take in a rates
        table from the pricing tool to calculate actual costs.

        Parameters
        ----------
        rates : nrel_p3.pricing_tool.Estimate.rates
            A rates pd.Series table from the Estimate object
        extra : dict
            If rate SLR categories are used in workday but not found in the
            pricing tool, you can enter extra options here, e.g.,
            {'NEW_SLR': 100}
        """
        for i, row in self.data.iterrows():
            slr = row['SLR']
            rate = np.nan
            if isinstance(extra, dict) and slr in extra:
                rate = extra[slr]
            elif isinstance(slr, str) and slr in rates:
                rate = rates[slr]

            self.data.at[i, 'cost'] = row['Total Hours (Time Tracking)'] * rate

    def actuals(self, filters=None):
        """Run the calculation of actual charges through time

        Parameters
        ----------
        filters : dict | None
            Set of filters where keys are columns in the estimate file and
            values are one or more items to sub select in the column.

        Returns
        -------
        actuals : pd.DataFrame
            An aggregated version of the workday actuals table with Year-Month
            index and columns: actual_cost, actual_cost_cumulative
        """

        subdf = self.data
        if filters is not None:
            subdf = filter(self.data, filters)

        actuals = subdf.groupby('Year-Month')[['cost']].sum()
        actuals['actual_cost_cumulative'] = actuals['cost'].cumsum()
        actuals = actuals.rename({'cost': 'actual_cost'}, axis=1)
        return actuals
