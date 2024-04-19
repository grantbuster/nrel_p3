"""
Interface with pricing tool csv export
"""
import re
import pandas as pd
from nrel_p3.utilities import filter, employee_id_regex


class Estimate:
    """Interface for pricing tool estimate

    To export a file from the NREL pricing tool, go to an estimate in the
    pricing tool and click on the the three lines button in the top right of an
    estimate and select: "Download Detailed CSV Dump"
    """

    DROP_LINE_ITEMS = ('Cross Cut Program Allocation',)

    def __init__(self, fp_csv):
        """
        Parameters
        ----------
        fp_csv : str
            Filepath to NREL Pricing Tool CSV export. Extract this by clicking
            the three lines button in the top right of an estimate and select:
            "Download Detailed CSV Dump"
        """
        self.data = pd.read_csv(fp_csv)

        drop_mask = ~self.data['LineItem'].isin(self.DROP_LINE_ITEMS)
        self.data = self.data[drop_mask]

        charge_codes = self.data['Effort'].apply(self.charge_code_regex)
        eids = self.data['Name/Note'].apply(employee_id_regex)

        self.data['charge_code'] = charge_codes
        self.data['eid'] = eids

    def __repr__(self):
        return self.data.__repr__()

    def __str__(self):
        return str(self.data)

    @staticmethod
    def charge_code_regex(text):
        """Get the charge code "12765.07.01.01" from text if the charge code is
        in the format: "GMLC.12765.07.01.01"

        Returns
        -------
        out : str | None
            Charge code string or None if not found
        """
        pattern = r'\b[A-Z]{4}\.(\d+\.\d+\.\d+\.\d+)'
        match = re.search(pattern, str(text))
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def get_employee_id(text):
        """Get the employee id from this format: "name, name (eid)"

        Returns
        -------
        out : str | None
            Employee ID in string format or None if not found
        """
        pattern = r'\((\d+)\)(?!.*\(\d+\))'
        match = re.search(pattern, str(text))
        if match:
            return match.group(1)
        else:
            return None

    def plan(self, filters=None):
        """Extract a timeseries plan for the project.

        Parameters
        ----------
        filters : dict | None
            Set of filters where keys are columns in the estimate file and
            values are one or more items to sub select in the column.

        Returns
        -------
        subdf : pd.DataFrame
            An aggregated version of the planning table with Year-Month index
            and columns: planned_cost, planned_cost_cumulative
        """

        if filters is not None:
            subdf = filter(self.data, filters)

        subdf = subdf.dropna(subset='LoadedCost')
        subdf = subdf.groupby('Year-Month').sum()
        subdf['LoadedCostCumulative'] = subdf['LoadedCost'].cumsum()
        subdf = subdf[['LoadedCost', 'LoadedCostCumulative']]
        name_map = {'LoadedCost': 'planned_cost',
                    'LoadedCostCumulative': 'planned_cost_cumulative'}
        subdf = subdf.rename(name_map, axis=1)
        return subdf

    @property
    def rates(self):
        """Get a employee cost-per-hour rates table where key is SLR category
        (e.g., TPRO1/LEAD2/MGMT1) and value is cost in $/hr

        Returns
        -------
        pd.Series
        """
        rates = self.data.groupby('SLR Category').sum()
        rates = rates['LoadedCost'] / rates['Hours']
        return rates
